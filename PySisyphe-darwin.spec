# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import collect_dynamic_libs

exclude = ['PyQt6']

datas = [('Sisyphe/doc/*.*', 'Sisyphe/doc'),
         ('Sisyphe/doc/_images/*.*', 'Sisyphe/doc/_images'),
         ('Sisyphe/doc/_sources/*.*', 'Sisyphe/doc/_sources'),
         ('Sisyphe/doc/_sources/API/*.*', 'Sisyphe/doc/_sources/API'),
         ('Sisyphe/doc/_static/*.*', 'Sisyphe/doc/_static'),
         ('Sisyphe/doc/_static/css/*.*', 'Sisyphe/doc/_static/css'),
         ('Sisyphe/doc/_static/css/fonts/*.*', 'Sisyphe/doc/_static/css/fonts'),
         ('Sisyphe/doc/_static/fonts/Lato/*.*', 'Sisyphe/doc/_static/fonts/Lato'),
         ('Sisyphe/doc/_static/fonts/RobotoSlab/*.*', 'Sisyphe/doc/_static/fonts/RobotoSlab'),
         ('Sisyphe/doc/_static/js/*.*', 'Sisyphe/doc/_static/js'),
         ('Sisyphe/doc/API/*.*', 'Sisyphe/doc/API'),
         ('Sisyphe/gui/baricons/*.*', 'Sisyphe/gui/baricons'),
         ('Sisyphe/gui/darkicons/*.*', 'Sisyphe/gui/darkicons'),
         ('Sisyphe/gui/darkroi/*.*', 'Sisyphe/gui/darkroi'),
         ('Sisyphe/gui/doc/*.*', 'Sisyphe/gui/doc'),
         ('Sisyphe/gui/font/*.*', 'Sisyphe/gui/font'),
         ('Sisyphe/gui/lighticons/*.*', 'Sisyphe/gui/lighticons'),
         ('Sisyphe/gui/lightroi/*.*', 'Sisyphe/gui/lightroi'),
         ('Sisyphe/gui/logos/*.*', 'Sisyphe/gui/logos'),
         ('Sisyphe/gui/lut/*.*', 'Sisyphe/gui/lut'),
         ('Sisyphe/gui/mesh/*.*', 'Sisyphe/gui/mesh'),
         ('Sisyphe/lib/db/models/*.*', 'Sisyphe/lib/db/models'),
         ('Sisyphe/plugins/*.*', 'Sisyphe/plugins'),
         ('Sisyphe/plugins/test/*.*', 'Sisyphe/plugins/test'),
         ('Sisyphe/processing/doc/*.*', 'Sisyphe/processing/doc'),
         ('Sisyphe/settings/*.*', 'Sisyphe/settings'),
         ('Sisyphe/templates/ANTSPYNET/*.*', 'Sisyphe/templates/ANTSPYNET'),
         ('Sisyphe/templates/ICBM152/*.*', 'Sisyphe/templates/ICBM152'),
         ('Sisyphe/templates/ICBM152/BUNDLES HCP/*.*', 'Sisyphe/templates/ICBM152/BUNDLES HCP'),
         ('Sisyphe/templates/ICBM152/BUNDLES HCP/TRACTS/*.*', 'Sisyphe/templates/ICBM152/BUNDLES HCP/TRACTS'),
         ('Sisyphe/templates/ICBM152/DESIKAN/*.*', 'Sisyphe/templates/ICBM152/DESIKAN'),
         ('Sisyphe/templates/ICBM152/DESIKAN/ATLAS/*.*', 'Sisyphe/templates/ICBM152/DESIKAN/ATLAS'),
         ('Sisyphe/templates/ICBM152/DESTRIEUX/*.*', 'Sisyphe/templates/ICBM152/DESTRIEUX'),
         ('Sisyphe/templates/ICBM152//DESTRIEUX/ATLAS/*.*', 'Sisyphe/templates/ICBM152/DESTRIEUX/ATLAS'),
         ('Sisyphe/templates/ICBM152/LABELLING/*.*', 'Sisyphe/templates/ICBM152/LABELLING'),
         ('Sisyphe/templates/ICBM152/PROJECTIONS/*.*', 'Sisyphe/templates/ICBM152/PROJECTIONS'),
         ('Sisyphe/widgets/icons/*.*', 'Sisyphe/widgets/icons'),
         ('venv/lib/python3.10/site-packages/dipy/data/files/*.*', 'dipy/data/files'),
         ('venv/lib/python3.10/site-packages/deepbrain/models/*.*', 'deepbrain/models'),
         ('venv/lib/python3.10/site-packages/itk/.dylibs/libtbb.12.3.dylib', 'itk/.dylibs/'),
         ('venv/lib/python3.10/site-packages/itk/ITKBridgeNumPyPython.py','itk'),
         ('venv/lib/python3.10/site-packages/itk/ITKCommonPython.py','itk'),
         ('venv/lib/python3.10/site-packages/itk/ITKPyBasePython.py','itk'),
         ('venv/lib/python3.10/site-packages/itk/support/__pycache__/build_options.pyc','itk/support'),
         ('venv/lib/python3.10/site-packages/vtkmodules/.dylibs/*.*','vtkmodules/.dylibs')]

binaries = collect_dynamic_libs('itk')
binaries += collect_dynamic_libs('vtkmodules')
binaries += collect_dynamic_libs('numpy')
binaries += collect_dynamic_libs('pandas')
binaries += collect_dynamic_libs('torch')
binaries += collect_dynamic_libs('sklearn')
binaries += collect_dynamic_libs('scipy')
binaries += collect_dynamic_libs('PyQt5')
binaries += collect_dynamic_libs('tensorflow')

hidden = collect_submodules('Sisyphe')
hidden += collect_submodules('ants')
hidden += collect_submodules('antspynet')
hidden += collect_submodules('dipy')
hidden += collect_submodules('itk')
hidden += collect_submodules('matplotlib')
hidden += collect_submodules('nibabel')
hidden += collect_submodules('nilearn')
hidden += collect_submodules('PyQt5')
hidden += collect_submodules('PyQtWebEngine')
hidden += collect_submodules('qtconsole')
hidden += collect_submodules('numpy')
hidden += collect_submodules('pandas')
hidden += collect_submodules('pydicom')
hidden += collect_submodules('pynetdicom')
hidden += collect_submodules('radiomics')
hidden += collect_submodules('SimpleITK')
hidden += collect_submodules('scipy')
hidden += collect_submodules('skimage')
hidden += collect_submodules('sklearn')
hidden += collect_submodules('darkdetect')
hidden += collect_submodules('qdarktheme')
hidden += collect_submodules('pywinstyles')
hidden += collect_submodules('docx')
hidden += collect_submodules('fpdf')
hidden += collect_submodules('Crypto')
hidden += collect_submodules('GPUtil')
hidden += collect_submodules('ipython')
hidden += collect_submodules('vtkmodules')
hidden += collect_submodules('easyocr')
hidden += collect_submodules('pymupdf')
hidden += collect_submodules('google')

a = Analysis(
    ['Sisyphe/PySisyphe.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=exclude,
    noarchive=True,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PySisyphe',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch='x86_64',
    codesign_identity=None,
    entitlements_file=None,
    icon=['pysisyphe.icns'],
    # hide_console='hide-early',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='PySisyphe',
)


