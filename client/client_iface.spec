# -*- mode: python -*-

# HAD TO ADD sdl2/bin TO PATH

from kivy.deps import sdl2, glew

block_cipher = None


a = Analysis(['..\\client_iface.py'],
             pathex=['specpath',
			 '.\\images'],
             binaries=[],
             datas=[],
             hiddenimports=['images'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
a.datas += [('client_iface.kv', '.\\client_iface.kv', 'DATA')]
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='client_iface',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )
coll = COLLECT(exe, Tree('.'),
               a.binaries,
               a.zipfiles,
               a.datas,
               *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
               strip=False,
               upx=True,
               name='client_iface')