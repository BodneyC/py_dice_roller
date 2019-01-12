# -*- mode: python -*-

from kivy.deps import sdl2, glew
import os

block_cipher = None

a = Analysis(
    ['client_iface.py'],
    # To build this on ones computer, the paths below obviously must be ammended
    pathex=['D:\\Users\\BenJC\\Documents\\2_Projects\\py_dice_roller\\client'],
    binaries=[('D:\\Users\\BenJC\\Documents\\2_Projects\\DnD\\py_dice_roller\\client\\SDL2.dll', '.')],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)
a.datas += [
    ('client_iface.kv', '.\\client_iface.kv', 'DATA'), 
    ('active.png', '.\\images\\active.png', 'DATA'),
    ('back.png', '.\\images\\back.png', 'DATA'),
    ('normal.png', '.\\images\\normal.png', 'DATA'),
    ('DroidSansMono.ttf', '.\\fonts\\DroidSansMono.ttf', 'DATA'),
]
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher
)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
    [],
    name='client_iface',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    console=False,
    icon='.\images\icon_dWU_icon.ico',
)
