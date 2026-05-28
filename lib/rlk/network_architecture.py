import torch
import torch.nn as nn
from .drop import DropPath

### MODEL

class Initial_block(nn.Module):

    def __init__(self, channels, group_num):
        super(Initial_block, self).__init__()

        self.gn1    = nn.GroupNorm(num_groups=group_num, num_channels=channels)
        self.act1   = nn.ReLU()
        self.conv1  = nn.Conv3d(channels, channels, 3, stride=1, padding=1)

        self.gn2    = nn.GroupNorm(num_groups=group_num, num_channels=channels)
        self.act2   = nn.ReLU()
        self.conv2  = nn.Conv3d(channels, channels, 3, stride=1, padding=1, groups=channels)

        self.gn3    = nn.GroupNorm(num_groups=group_num, num_channels=channels)
        self.act3   = nn.ReLU()
        self.conv3  = nn.Conv3d(channels, channels, 1, stride=1, padding=0)

        self.gn4    = nn.GroupNorm(num_groups=group_num, num_channels=channels)
        self.act4   = nn.ReLU()
        self.conv4  = nn.Conv3d(channels, channels, 3, stride=1, padding=1, groups=channels)

    def forward(self, x):
        y   = self.conv1(self.act1(self.gn1(x)))
        y   = self.conv2(self.act2(self.gn2(y)))
        y   = self.conv3(self.act3(self.gn3(y)))
        y   = self.conv4(self.act4(self.gn4(y)))
        return y


class LargeKernelReparam(nn.Module):

    def __init__(self, channels, kernel, small_kernels=()):
        super(LargeKernelReparam, self).__init__()

        self.dw_large       = nn.Conv3d(channels, channels, kernel, padding=kernel//2, groups=channels)

        self.small_kernels  = small_kernels
        for k in self.small_kernels:
            setattr(self, f"dw_small_{k}", nn.Conv3d(channels, channels, k, padding=k//2, groups=channels))

    def forward(self, in_p):
        out_p        = self.dw_large(in_p)
        for k in self.small_kernels:
            out_p    += getattr(self, f"dw_small_{k}")(in_p)
        return out_p        


class encblock(nn.Module):

    def __init__(self, channels, group_num, kernel=13, small_kernels=(5,), mlp_ratio=4.0, drop=0.3, drop_path=0.5):
        super(encblock, self).__init__()
        self.kernel         = kernel
        self.small_kernels  = small_kernels
        self.drop           = drop
        self.drop_path      = drop_path

        self.gn1            = nn.GroupNorm(num_groups=group_num, num_channels=channels)
        self.act1           = nn.ReLU()
        self.conv1          = nn.Conv3d(channels, channels, 1, stride=1, padding=0)

        self.gn2            = nn.GroupNorm(num_groups=group_num, num_channels=channels)
        self.act2           = nn.ReLU()
        self.lkr2           = LargeKernelReparam(channels, self.kernel, self.small_kernels)

        self.gn3            = nn.GroupNorm(num_groups=group_num, num_channels=channels)
        self.act3           = nn.ReLU()
        self.conv3          = nn.Conv3d(channels, channels, 1, stride=1, padding=0)

        self.gn4            = nn.GroupNorm(num_groups=group_num, num_channels=channels)
        self.act4           = nn.GELU()
        self.mlp4           = nn.Conv3d(channels, int(channels*mlp_ratio), 1, stride=1, padding=0)

        self.gn5            = nn.GroupNorm(num_groups=group_num, num_channels=int(channels*mlp_ratio))
        self.act5           = nn.GELU()
        self.mlp5           = nn.Conv3d(int(channels*mlp_ratio), channels, 1, stride=1, padding=0)

        self.dropout        = nn.Dropout(self.drop)
        self.droppath       = DropPath(self.drop_path) if self.drop_path > 0. else nn.Identity()

    def forward(self, x):
        y   = self.conv1(self.act1(self.gn1(x)))
        y   = self.lkr2(self.act2(self.gn2(y)))
        y   = self.conv3(self.act3(self.gn3(x)))
        x   = x + self.droppath(y)

        y   = self.mlp4(self.act4(self.gn4(x)))
        y   = self.dropout(y)
        y   = self.mlp5(self.act5(self.gn5(y)))
        y   = self.dropout(y)
        x   = x + self.droppath(y)
        return x


class DownSample(nn.Module):

    def __init__(self, in_channels, out_channels, group_num):
        super(DownSample, self).__init__()

        self.gn1    = nn.GroupNorm(num_groups=group_num, num_channels=in_channels)
        self.act1   = nn.ReLU()
        self.conv1  = nn.Conv3d(in_channels, out_channels, 1)

        self.gn2    = nn.GroupNorm(num_groups=group_num, num_channels=out_channels)
        self.act2   = nn.ReLU()
        self.conv2  = nn.Conv3d(out_channels, out_channels, 3, stride=2, padding=1, groups=out_channels) #안되면 group 뺴고 해보기
    
    def forward(self, x):
        y   = self.conv1(self.act1(self.gn1(x)))
        y   = self.conv2(self.act2(self.gn2(y)))
        return y


class UpSample(nn.Module):

    def __init__(self, in_channels, out_channels, group_num):
        super(UpSample, self).__init__()

        self.gn1    = nn.GroupNorm(num_groups=group_num, num_channels=in_channels)
        self.act1   = nn.ReLU()
        self.conv1  = nn.Conv3d(in_channels, out_channels, 1)

        self.gn2    = nn.GroupNorm(num_groups=group_num, num_channels=out_channels)
        self.act2   = nn.ReLU()
        self.up2    = nn.ConvTranspose3d(out_channels, out_channels, 2, stride=2, groups=out_channels) #안되면 groups 빼고 해보기

    def forward(self, x):
        y   = self.conv1(self.act1(self.gn1(x)))
        y   = self.up2(self.act2(self.gn2(y)))
        return y


class decblock(nn.Module):

    def __init__(self, in_channels, out_channels, group_num):
        super(decblock, self).__init__()

        self.gn1    = nn.GroupNorm(num_groups=group_num, num_channels=in_channels)
        self.relu1  = nn.ReLU()
        self.conv1  = nn.Conv3d(in_channels, out_channels, 3, stride=1, padding=1)

        self.gn2    = nn.GroupNorm(num_groups=group_num, num_channels=out_channels)
        self.relu2  = nn.ReLU()
        self.conv2  = nn.Conv3d(out_channels, out_channels, 3, stride=1, padding=1, groups=out_channels)

    def forward(self, x):
        y   = self.conv1(self.relu1(self.gn1(x)))
        y   = self.conv2(self.relu2(self.gn2(y)))
        return y


class RLKunet(nn.Module):

    def __init__(self, in_channels=1, out_channels=2, features=14, group_num=7):
        super(RLKunet, self).__init__()

        self.init_conv  = nn.Conv3d(in_channels, features, 1, stride=1, padding=0)
        self.init_block = Initial_block(features, group_num)

        self.encoder1_1 = encblock(features, group_num, drop_path=0.0)
        self.encoder1_2 = encblock(features, group_num, drop_path=0.0)
        self.down1      = DownSample(features, features*2, group_num)

        self.encoder2_1 = encblock(features*2, group_num, drop_path=0.2)
        self.encoder2_2 = encblock(features*2, group_num, drop_path=0.2)
        self.down2      = DownSample(features*2, features*4, group_num)

        self.encoder3_1 = encblock(features*4, group_num, drop_path=0.3)
        self.encoder3_2 = encblock(features*4, group_num, drop_path=0.3)
        self.down3      = DownSample(features*4, features*8, group_num)

        self.encoder4_1 = encblock(features*8, group_num, drop_path=0.5)
        self.encoder4_2 = encblock(features*8, group_num, drop_path=0.5)
        self.encoder4_3 = encblock(features*8, group_num, drop_path=0.5)
        self.encoder4_4 = encblock(features*8, group_num, drop_path=0.5)

        self.up3        = UpSample(features*8, features*4, group_num)
        self.decoder3_1 = decblock(features*(4+4), features*4, group_num)
        self.decoder3_2 = decblock(features*4, features*4, group_num)

        self.up2        = UpSample(features*4, features*2, group_num)
        self.decoder2_1 = decblock(features*(2+2), features*2, group_num)
        self.decoder2_2 = decblock(features*2, features*2, group_num)

        self.up1        = UpSample(features*2, features, group_num)
        self.decoder1_1 = decblock(features*(1+1), features, group_num)
        self.decoder1_2 = decblock(features, features, group_num)

        self.conv       = nn.Conv3d(features, out_channels, 1, stride=1 , padding=0)
        self.softmax    = nn.Softmax(dim=1)

        # highlight foreground
        self.hfconv4    = nn.Conv3d(features*8, out_channels, 1, stride=1, padding=0)
        self.hfconv3    = nn.Conv3d(features*4, out_channels, 1, stride=1, padding=0)
        self.hfconv2    = nn.Conv3d(features*2, out_channels, 1, stride=1, padding=0)

    def forward(self, x):                       # batch, 1, H, W, D
        enc0_1      = self.init_conv(x)         # batch, 14, H, W, D
        enc0_2      = self.init_block(enc0_1) 

        enc1_1      = self.encoder1_1(enc0_2)    
        enc1_2      = self.encoder1_2(enc1_1)  
        dwn1        = self.down1(enc1_2)        # batch, 28, H/2, W/2, D/2

        enc2_1      = self.encoder2_1(dwn1)    
        enc2_2      = self.encoder2_2(enc2_1)  
        dwn2        = self.down2(enc2_2)        # batch, 56, H/4, W/4, D/4

        enc3_1      = self.encoder3_1(dwn2)    
        enc3_2      = self.encoder3_2(enc3_1)  
        dwn3        = self.down3(enc3_2)        # batch, 112, H/8, W/8, D/8

        enc4_1      = self.encoder4_1(dwn3)    
        enc4_2      = self.encoder4_2(enc4_1)  
        enc4_3      = self.encoder4_3(enc4_2)  
        enc4_4      = self.encoder4_4(enc4_3)  

        up3         = self.up3(enc4_4)                  # batch, 128, H/4, W/4, D/4
        concat3     = torch.cat((enc3_2, up3), dim=1)   # batch, 128+64, H/4, W/4, D/4
        dec3_1      = self.decoder3_1(concat3)          # batch, 64, H/4, W/4, D/4
        dec3_2      = self.decoder3_2(dec3_1)

        up2         = self.up2(dec3_2)                  # batch, 64, H/2, W/2, D/2
        concat2     = torch.cat((enc2_2, up2), dim=1)   # batch, 64+32, H/2, W/2, D/2
        dec2_1      = self.decoder2_1(concat2)          # batch, 32, H/2, W/2, D/2
        dec2_2      = self.decoder2_2(dec2_1)

        up1         = self.up1(dec2_2)                  # batch, 32, H, W, D
        concat1     = torch.cat((enc1_2, up1), dim=1)   # batch, 32+16, H, W, D
        dec1_1      = self.decoder1_1(concat1)          # batch, 16, H, W, D
        dec1_2      = self.decoder1_2(dec1_1)

        dec1_out    = self.conv(dec1_2)                 # batch, 2, H, W, D
        out1        = self.softmax(dec1_out)

        # highlight foreground
        out4        = self.softmax(self.hfconv4(enc4_4))
        out3        = self.softmax(self.hfconv3(dec3_2))
        out2        = self.softmax(self.hfconv2(dec2_2))
        return out4, out3, out2, out1