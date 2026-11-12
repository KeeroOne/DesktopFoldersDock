import sys
import os
import re
import math
import time
import json
import shutil
import winreg
import hashlib
import urllib.parse
import urllib.request
import webbrowser
import subprocess
import ctypes
from ctypes import wintypes
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QMenu, QFileDialog, QInputDialog, QPushButton, QFrame,
    QFileIconProvider, QSystemTrayIcon, QStyle, QScrollArea,
    QGraphicsDropShadowEffect, QDialog, QGridLayout, QSpinBox,
    QFormLayout, QSlider, QComboBox, QCheckBox, QColorDialog,
    QTabWidget, QMessageBox, QToolTip
)
from PyQt6.QtCore import (
    Qt, QPoint, QPointF, QSize, QFileInfo, QRectF, QPropertyAnimation,
    QEasingCurve, QTimer, QThread, pyqtSignal, QAbstractNativeEventFilter
)
from PyQt6.QtGui import (
    QPixmap, QIcon, QPainter, QColor, QFont, QCursor,
    QLinearGradient, QPen, QImage, QPainterPath, QPolygonF
)


APP_NAME = "DesktopFoldersDock"
APP_TITLE = "Desktop Folders Dock"
APP_VERSION = "1.7"

CLOUDTIPS_URL = "https://pay.cloudtips.ru/p/ac9cc579"
DONATEPAY_URL = "https://donatepay.ru/don/1542831"
GITHUB_URL = "https://github.com/KeeroOne/DesktopFoldersDock"



if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
    if not os.path.exists(BASE_DIR):
        BASE_DIR = os.path.dirname(sys.executable)
    EXE_PATH = f'"{os.path.abspath(sys.argv[0])}"'
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    runner = pythonw if os.path.exists(pythonw) else sys.executable
    EXE_PATH = f'"{runner}" "{os.path.abspath(__file__)}"'

APPDATA_DIR = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
    APP_NAME
)


def is_dir_writable(dir_path: str) -> bool:
    try:
        os.makedirs(dir_path, exist_ok=True)
        test_file = os.path.join(dir_path, ".write_test_tmp")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(test_file)
        return True
    except Exception:
        return False


if is_dir_writable(BASE_DIR):
    DATA_DIR = BASE_DIR
else:
    os.makedirs(APPDATA_DIR, exist_ok=True)
    DATA_DIR = APPDATA_DIR
    bundled_cfg = os.path.join(BASE_DIR, "folders_config.json")
    appdata_cfg = os.path.join(DATA_DIR, "folders_config.json")
    if os.path.exists(bundled_cfg) and not os.path.exists(appdata_cfg):
        try:
            shutil.copy2(bundled_cfg, appdata_cfg)
        except Exception:
            pass

CONFIG_FILE = os.path.join(DATA_DIR, "folders_config.json")
BUNDLED_ICONS_DIR = os.path.join(BASE_DIR, "icons")
USER_ICONS_DIR = os.path.join(DATA_DIR, "icons")
DISK_ICON_CACHE_DIR = os.path.join(DATA_DIR, "icon_cache")
os.makedirs(USER_ICONS_DIR, exist_ok=True)
os.makedirs(DISK_ICON_CACHE_DIR, exist_ok=True)
ICONS_DIR = BUNDLED_ICONS_DIR if is_dir_writable(BUNDLED_ICONS_DIR) else USER_ICONS_DIR


def get_installer_language_from_registry() -> str:
    for arg in sys.argv:
        if arg.lower() in ("--lang=en", "/lang=en"):
            return "en"
        if arg.lower() in ("--lang=ru", "/lang=ru"):
            return "ru"
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            rf"Software\{APP_NAME}",
            0, winreg.KEY_READ
        )
        val, _ = winreg.QueryValueEx(key, "Language")
        winreg.CloseKey(key)
        if val in ("ru", "en"):
            return val
    except Exception:
        pass
    return "ru"


def save_language_to_registry(lang: str):
    try:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\{APP_NAME}")
        winreg.SetValueEx(key, "Language", 0, winreg.REG_SZ, lang)
        winreg.CloseKey(key)
    except Exception:
        pass



_CURRENT_LANG = get_installer_language_from_registry()

TRANSLATIONS = {
    "ru": {
        "about_title": "О программе",
        "version_lbl": "Версия",
        "about_desc": "Кастомная интерактивная док-панель папок\nи быстрого запуска для Windows 10 / 11.",
        "support_header": "Поддержать автора и проект:",
        "github_btn": "Проект на GitHub",
        "close_btn": "Закрыть",
        "done_btn": "Готово",
        "settings_win_title": "Настройки",
        "tab_panel": "Панель и Темы",
        "tab_folders": "Папки и вид",
        "tab_popup": "Выпадающий список",
        "tab_system": "Поведение и система",
        "tab_about": "О программе",
        "cfg_file_lbl": "Файл настроек:",
        "mode_h": "Горизонтальная панель (раскрытие вниз)",
        "mode_v": "Вертикальная панель (раскрытие вбок)",
        "mode_free": "Свободные папки (по одной на экране)",
        "shape_rounded": "Скругленная капсула (Стандарт)",
        "shape_hexagon": "Шестигранник < === > (Боковые скосы)",
        "shape_trap_up": "Трапеция \\___/ (Скос вниз)",
        "shape_trap_down": "Трапеция /‾‾‾\\ (Скос вверх)",
        "shape_chamfer": "Срезанные углы (Восьмиугольник)",
        "shape_rect": "Прямоугольник",
        "anim_wave": "Волна (Увеличение + соседи меньше)",
        "anim_float": "Левитация (Всплытие вверх + неон)",
        "anim_spring": "Упругий прыжок (Пружина)",
        "anim_pulse": "Неоновое дыхание (Пульсация)",
        "anim_zoom": "Плавный зум (Только выбранная)",
        "anim_tilt": "3D-качание (Наклон при наведении)",
        "anim_none": "Без анимации (Только подсветка)",
        "hk_alt_space": "Alt + Пробел (Рекомендуется в играх)",
        "hk_ctrl_tilde": "Ctrl + ~ (Тильда / Ё)",
        "hk_alt_tilde": "Alt + ~ (Тильда / Ё)",
        "hk_alt_q": "Alt + Q",
        "hk_ctrl_shift_d": "Ctrl + Shift + D",
        "hk_win_z": "Win + Z",
        "hk_f10": "Клавиша F10",
        "hk_none": "Отключено",
        "lbl_global_theme": "Глобальная тема оформления:",
        "btn_save_theme": "Сохранить текущие цвета как тему...",
        "btn_del_theme": "Удалить тему",
        "dlg_save_theme_t": "Сохранить свою тему",
        "dlg_save_theme_l": "Введите название для новой цветовой темы:",
        "lbl_layout_mode": "Режим расположения:",
        "lbl_dock_shape": "Форма панели:",
        "lbl_dock_slant": "Скос боковых граней:",
        "lbl_corner_radius": "Скругление углов фигуры:",
        "lbl_dock_bg_col": "Цвет фона панели:",
        "lbl_dock_opacity": "Непрозрачность панели:",
        "lbl_edge_fade": "Затухание у краёв (%):",
        "lbl_border_col": "Цвет рамки контура:",
        "lbl_border_opacity": "Яркость рамки контура:",
        "cb_show_dock_bg": "Показывать общую фоновую подложку панели",
        "cb_edge_fade": "Плавное затухание прозрачности панели к краям",
        "cb_accent_border": "Окрашивать рамку панели в акцентный цвет",
        "cb_sync_all": "Применять размер, цвета и шрифт сразу КО ВСЕМ папкам",
        "lbl_folder_size": "Размер плитки папок (пикс.):",
        "lbl_folder_font": "Размер шрифта подписи (пт):",
        "font_auto": "Авто (по размеру)",
        "lbl_theme": "Цветовая тема папок:",
        "lbl_custom_tile_bg": "Свой цвет фона папок:",
        "lbl_custom_tile_acc": "Свой цвет рамки папок:",
        "btn_pick_tile_bg": "Выбрать свой цвет плитки из палитры...",
        "btn_pick_tile_acc": "Выбрать свой цвет рамки папок из палитры...",
        "cb_icon_only": "Только иконка (без фоновой плитки под папкой)",
        "cb_show_title": "Показывать текстовую подпись под папкой",
        "cb_show_badge": "Показывать счётчик количества программ",
        "cb_fav_folder": "Показывать специальную папку «Избранное» (для папок)",
        "pm_multi": "Вместить всё разом (Несколько колонок)",
        "pm_grid": "Режим «Плитки (Grid)» (Сетка иконок)",
        "pm_scroll": "Одиночный список с прокруткой",
        "lbl_pop_mode": "Режим отображения списка:",
        "lbl_pop_w": "Ширина колонки списка (пикс.):",
        "lbl_pop_ic": "Размер иконок в списке (пикс.):",
        "lbl_pop_fn": "Размер шрифта списка (пт):",
        "lbl_pop_rows": "Программ в 1 столбце (мульти):",
        "lbl_pop_grid": "Колонок в режиме «Плитки (Grid)»:",
        "lbl_pop_maxh": "Макс. высота (режим прокрутки):",
        "lbl_pop_col": "Цвет фона всплывающего окна:",
        "lbl_pop_opacity": "Непрозрачность всплыв. окна:",
        "lbl_lang": "Язык интерфейса (Language):",
        "lbl_anim_style": "Стиль анимации при наведении:",
        "lbl_hotkey": "Вызов панели поверх игр (Хоткей):",
        "hk_hint": "Удержание ЛКМ на папке (0.45 с) включает режим перемещения папок.\nПо нажатию горячей клавиши панель появляется поверх игры до выбора ярлыка.",
        "cb_hover_open": "Открывать выпадающий список при наведении мыши",
        "cb_autohide": "Автоскрытие панели за край экрана",
        "cb_run_ind": "Показывать зеленый индикатор запущенных программ",
        "cb_always_top": "Всегда поверх всех окон (Постоянно)",
        "cb_autostart": "Запускать автоматически вместе с Windows",
        "btn_rescan": "Пересканировать ярлыки",
        "btn_open_icons": "Папка с иконками (icons)",
        "btn_export_cfg": "Экспорт настроек...",
        "btn_import_cfg": "Импорт настроек...",
        "dlg_export_t": "Экспорт настроек в файл",
        "dlg_import_t": "Импорт настроек из файла",
        "json_filter": "Файлы настроек JSON (*.json)",
        "msg_export_ok": "Настройки успешно экспортированы!",
        "msg_import_ok": "Настройки успешно загружены!",
        "palette_btn": "Палитра",
        "gallery_title": "Галерея иконок (папка icons)",
        "gallery_pack_dir": "Папка пака:",
        "btn_open_folder": "Открыть папку",
        "gallery_empty": "В папке «icons» пока нет картинок.\n\nЗакиньте туда свои PNG-иконки и снова откройте это окно!",
        "btn_browse_other": "Выбрать файл с другого места...",
        "dlg_pick_icon": "Выберите иконку",
        "img_filter": "Изображения (*.png *.ico *.webp *.jpg *.jpeg *.bmp *.svg)",
        "btn_sort_tip": "Отсортировать ярлыки по имени (А-Я / Я-А)",
        "btn_grid": "Плитки",
        "btn_list": "Список",
        "btn_add_sep": "+ Разделитель",
        "btn_add_sep_tip": "Добавить горизонтальный разделитель в список",
        "btn_add_web": "+ Сайт",
        "btn_add_web_tip": "Добавить ссылку на локальную веб-панель или сайт",
        "btn_add_dir": "+ Папка",
        "btn_add_file": "+ Файл",
        "empty_fav_hint": "Перетащите сюда папки или ссылки\nили нажмите «+ Папка» / «+ Сайт»",
        "empty_reg_hint": "Перетащите сюда ярлыки, папки или URL\nили используйте кнопки сверху",
        "ctx_edit_url": "Изменить URL-адрес ссылки...",
        "ctx_run_admin": "Запустить от имени Администратора",
        "ctx_open_loc": "Открыть расположение в Проводнике",
        "ctx_change_item_ic": "Сменить иконку элемента...",
        "ctx_move_to_folder": "Отправить в другую папку",
        "ctx_add_sep_here": "Вставить разделитель ниже",
        "ctx_sort_az": "Отсортировать весь список по имени",
        "ctx_move_up": "Поднять выше",
        "ctx_move_down": "Опустить ниже",
        "ctx_rename": "Переименовать",
        "ctx_delete_item": "Удалить из списка",
        "dlg_sep_t": "Добавить разделитель",
        "dlg_sep_l": "Текст на разделителе (оставьте пустым для простой линии):",
        "dlg_img_drop_t": "Изображение перетащено на папку",
        "dlg_img_drop_q": "Сделать файл «{0}» иконкой этой папки?\n\n(Нажмите «Да» — чтобы сменить иконку папки,\n«Нет» — чтобы добавить картинку как файл в список)",
        "dlg_edit_url_t": "Изменить адрес",
        "dlg_edit_url_l": "URL веб-панели или сайта:",
        "dlg_pick_app": "Выберите программу или ярлык",
        "app_filter": "Программы и ярлыки (*.exe *.lnk *.bat *.url);;Все файлы (*.*)",
        "dlg_app_name_t": "Название программы",
        "dlg_app_name_l": "Как подписать программу в списке?",
        "dlg_pick_dir": "Выберите папку для добавления в список",
        "dlg_dir_name_t": "Название папки",
        "dlg_dir_name_l": "Как подписать папку в списке?",
        "dlg_web_t": "Добавить веб-панель или сайт",
        "dlg_web_l": "Введите адрес (например, 192.168.1.1:8080 или https://...):",
        "dlg_web_name_t": "Название ссылки",
        "dlg_web_name_l": "Как подписать веб-панель или сайт в списке?",
        "dlg_rename_l": "Новое название:",
        "dlg_folder_name_l": "Введите название папки:",
        "tray_show_top": "Показать поверх окон (Временно)",
        "edit_done": "Готово (Завершить редактирование)",
        "edit_start": "Редактировать панель (Перемещение)",
        "ctx_center_dock": "Отцентровать панель на экране",
        "ctx_rescan": "Пересканировать ярлыки и иконки",
        "tray_autostart": "Запускать вместе с Windows",
        "menu_settings": "Настройки...",
        "menu_about": "О программе",
        "menu_quit": "Выход",
        "menu_close_app": "Закрыть программу",
        "ctx_pick_folder_ic": "Выбрать иконку папки...",
        "ctx_add_app": "Добавить программу / ярлык...",
        "ctx_add_dir": "Добавить папку-ссылку...",
        "ctx_add_web": "Добавить веб-панель / сайт...",
        "ctx_rename_folder": "Переименовать эту папку",
        "ctx_new_folder": "Добавить новую папку",
        "ctx_del_folder": "Удалить эту папку",
        "def_fav_title": "Избранное",
        "def_downloads": "Загрузки",
        "def_documents": "Документы",
        "def_shortcut": "Ярлык",
        "def_notepad": "Блокнот",
        "def_calc": "Калькулятор",
        "theme_win11": "Тёмное стекло (Win 11)",
        "theme_ocean": "Глубокий океан",
        "theme_violet": "Неоновый фиолет",
        "theme_forest": "Изумрудный лес",
        "theme_graphite": "Тёплый графит",
        "theme_sunset": "Малиновый закат",
        "theme_gold": "Золотое Избранное",
        "theme_light": "Светлый минимализм (Light)",
        "theme_cyber": "Киберпанк Неон",
        "theme_custom": "Свой цвет (Вручную)",
    },
    "en": {
        "about_title": "About",
        "version_lbl": "Version",
        "about_desc": "Custom interactive desktop folder dock\nand quick application launcher for Windows 10 / 11.",
        "support_header": "Support the developer & project:",
        "github_btn": "Project on GitHub",
        "close_btn": "Close",
        "done_btn": "Done",
        "settings_win_title": "Settings",
        "tab_panel": "Dock & Themes",
        "tab_folders": "Folders & View",
        "tab_popup": "Dropdown List",
        "tab_system": "Behavior & System",
        "tab_about": "About",
        "cfg_file_lbl": "Config file:",
        "mode_h": "Horizontal Dock (Opens downward)",
        "mode_v": "Vertical Dock (Opens sideways)",
        "mode_free": "Standalone Folders (Free placement)",
        "shape_rounded": "Rounded Pill (Standard)",
        "shape_hexagon": "Hexagon < === > (Angled sides)",
        "shape_trap_up": "Trapezoid \\___/ (Slanted down)",
        "shape_trap_down": "Trapezoid /‾‾‾\\ (Slanted up)",
        "shape_chamfer": "Chamfered Corners (Octagon)",
        "shape_rect": "Rectangle",
        "anim_wave": "MacOS Wave (Zoom + neighbors shrink)",
        "anim_float": "Levitation (Float up + neon glow)",
        "anim_spring": "Spring Bounce (Elastic zoom)",
        "anim_pulse": "Neon Breathing (Pulse)",
        "anim_zoom": "Smooth Zoom (Hovered folder only)",
        "anim_tilt": "3D Tilt (Slight rotation on hover)",
        "anim_none": "No Animation (Border highlight only)",
        "hk_alt_space": "Alt + Space (Recommended for games)",
        "hk_ctrl_tilde": "Ctrl + ~ (Tilde)",
        "hk_alt_tilde": "Alt + ~ (Tilde)",
        "hk_alt_q": "Alt + Q",
        "hk_ctrl_shift_d": "Ctrl + Shift + D",
        "hk_win_z": "Win + Z",
        "hk_f10": "F10 Key",
        "hk_none": "Disabled",
        "lbl_global_theme": "Global Color Theme:",
        "btn_save_theme": "Save current colors as theme...",
        "btn_del_theme": "Delete Theme",
        "dlg_save_theme_t": "Save Custom Theme",
        "dlg_save_theme_l": "Enter a name for your color theme:",
        "lbl_layout_mode": "Layout Mode:",
        "lbl_dock_shape": "Dock Shape:",
        "lbl_dock_slant": "Side Slant Angle:",
        "lbl_corner_radius": "Shape Corner Rounding:",
        "lbl_dock_bg_col": "Dock Background Color:",
        "lbl_dock_opacity": "Dock Opacity:",
        "lbl_edge_fade": "Edge Fade Strength (%):",
        "lbl_border_col": "Border Outline Color:",
        "lbl_border_opacity": "Border Outline Opacity:",
        "cb_show_dock_bg": "Show common dock background plate",
        "cb_edge_fade": "Smoothly fade dock transparency near edges",
        "cb_accent_border": "Colorize dock border with theme accent color",
        "cb_sync_all": "Apply size, colors, and font to ALL folders at once",
        "lbl_folder_size": "Folder Tile Size (px):",
        "lbl_folder_font": "Title Font Size (pt):",
        "font_auto": "Auto (fit to size)",
        "lbl_theme": "Folder Color Preset:",
        "lbl_custom_tile_bg": "Custom Folder Background:",
        "lbl_custom_tile_acc": "Custom Folder Border Color:",
        "btn_pick_tile_bg": "Pick custom tile color from palette...",
        "btn_pick_tile_acc": "Pick custom border color from palette...",
        "cb_icon_only": "Icon only (hide tile background plate)",
        "cb_show_title": "Show text caption under folder",
        "cb_show_badge": "Show app counter badge",
        "cb_fav_folder": "Show special 'Favorites' folder (for folder links)",
        "pm_multi": "Fit All at Once (Multi-column view)",
        "pm_grid": "Grid Mode (Icon tiles)",
        "pm_scroll": "Single Column with Scrollbar",
        "lbl_pop_mode": "Dropdown Display Mode:",
        "lbl_pop_w": "Column Width (px):",
        "lbl_pop_ic": "List Icon Size (px):",
        "lbl_pop_fn": "List Font Size (pt):",
        "lbl_pop_rows": "Items per Column (Multi-col):",
        "lbl_pop_grid": "Columns in Grid Mode:",
        "lbl_pop_maxh": "Max Height (Scroll mode):",
        "lbl_pop_col": "Popup Background Color:",
        "lbl_pop_opacity": "Popup Background Opacity:",
        "lbl_lang": "Interface Language (Язык):",
        "lbl_anim_style": "Hover Animation Style:",
        "lbl_hotkey": "In-Game Overlay Hotkey:",
        "hk_hint": "Hold Left Click on a folder (0.45s) to enter move/reorder mode.\nPress the hotkey to summon the dock above fullscreen games.",
        "cb_hover_open": "Open dropdown list on mouse hover",
        "cb_autohide": "Auto-hide dock at screen edges",
        "cb_run_ind": "Show green indicator for running apps",
        "cb_always_top": "Always on Top (Permanent)",
        "cb_autostart": "Start automatically with Windows",
        "btn_rescan": "Rescan Shortcuts",
        "btn_open_icons": "Open 'icons' Folder",
        "btn_export_cfg": "Export Settings...",
        "btn_import_cfg": "Import Settings...",
        "dlg_export_t": "Export Settings to File",
        "dlg_import_t": "Import Settings from File",
        "json_filter": "JSON Settings Files (*.json)",
        "msg_export_ok": "Settings exported successfully!",
        "msg_import_ok": "Settings imported successfully!",
        "palette_btn": "Palette",
        "gallery_title": "Icon Gallery ('icons' folder)",
        "gallery_pack_dir": "Pack folder:",
        "btn_open_folder": "Open Folder",
        "gallery_empty": "No images in the 'icons' folder yet.\n\nDrop your PNG icons there and reopen this window!",
        "btn_browse_other": "Browse file from another location...",
        "dlg_pick_icon": "Select Icon",
        "img_filter": "Images (*.png *.ico *.webp *.jpg *.jpeg *.bmp *.svg)",
        "btn_sort_tip": "Sort items by name (A-Z / Z-A)",
        "btn_grid": "Grid",
        "btn_list": "List",
        "btn_add_sep": "+ Divider",
        "btn_add_sep_tip": "Add a horizontal divider line to the list",
        "btn_add_web": "+ Web",
        "btn_add_web_tip": "Add link to local web panel or website",
        "btn_add_dir": "+ Folder",
        "btn_add_file": "+ App",
        "empty_fav_hint": "Drag folders or links here from Explorer\nor click '+ Folder' / '+ Web'",
        "empty_reg_hint": "Drag shortcuts, folders, or URLs here\nor use the buttons above",
        "ctx_edit_url": "Edit URL address...",
        "ctx_run_admin": "Run as Administrator",
        "ctx_open_loc": "Open File Location in Explorer",
        "ctx_change_item_ic": "Change Item Icon...",
        "ctx_move_to_folder": "Send to Another Folder",
        "ctx_add_sep_here": "Insert Divider Below",
        "ctx_sort_az": "Sort entire list by name (A-Z)",
        "ctx_move_up": "Move Up",
        "ctx_move_down": "Move Down",
        "ctx_rename": "Rename",
        "ctx_delete_item": "Remove from List",
        "dlg_sep_t": "Add Divider",
        "dlg_sep_l": "Divider label (leave blank for a simple line):",
        "dlg_img_drop_t": "Image Dropped on Folder",
        "dlg_img_drop_q": "Set '{0}' as this folder's icon?\n\n(Click 'Yes' to set as folder icon,\n'No' to add the image file to the list)",
        "dlg_edit_url_t": "Edit URL",
        "dlg_edit_url_l": "Web panel or website URL:",
        "dlg_pick_app": "Select Application or Shortcut",
        "app_filter": "Applications & Shortcuts (*.exe *.lnk *.bat *.url);;All Files (*.*)",
        "dlg_app_name_t": "Application Name",
        "dlg_app_name_l": "Display name in the list:",
        "dlg_pick_dir": "Select Folder to Add as Link",
        "dlg_dir_name_t": "Folder Name",
        "dlg_dir_name_l": "Display name in the list:",
        "dlg_web_t": "Add Web Panel or Website",
        "dlg_web_l": "Enter address (e.g., 192.168.1.1:8080 or https://...):",
        "dlg_web_name_t": "Link Name",
        "dlg_web_name_l": "Display name in the list:",
        "dlg_rename_l": "New name:",
        "dlg_folder_name_l": "Enter folder title:",
        "tray_show_top": "Bring to Front (Temporary)",
        "edit_done": "Done (Exit Edit Mode)",
        "edit_start": "Edit Dock (Move / Reorder)",
        "ctx_center_dock": "Center Dock on Screen",
        "ctx_rescan": "Rescan Shortcuts & Icons",
        "tray_autostart": "Start with Windows",
        "menu_settings": "Settings...",
        "menu_about": "About",
        "menu_quit": "Exit",
        "menu_close_app": "Quit Application",
        "ctx_pick_folder_ic": "Choose Folder Icon...",
        "ctx_add_app": "Add Application / Shortcut...",
        "ctx_add_dir": "Add Folder Link...",
        "ctx_add_web": "Add Web Panel / Website...",
        "ctx_rename_folder": "Rename Folder",
        "ctx_new_folder": "Add New Folder",
        "ctx_del_folder": "Delete This Folder",
        "def_fav_title": "Favorites",
        "def_downloads": "Downloads",
        "def_documents": "Documents",
        "def_shortcut": "Folder",
        "def_notepad": "Notepad",
        "def_calc": "Calculator",
        "theme_win11": "Dark Glass (Win 11)",
        "theme_ocean": "Deep Ocean",
        "theme_violet": "Neon Violet",
        "theme_forest": "Emerald Forest",
        "theme_graphite": "Warm Graphite",
        "theme_sunset": "Crimson Sunset",
        "theme_gold": "Golden Favorites",
        "theme_light": "Light Minimal (Light)",
        "theme_cyber": "Cyberpunk Neon",
        "theme_custom": "Custom Color (Manual)",
    }
}


def tr(key: str) -> str:
    lang_dict = TRANSLATIONS.get(_CURRENT_LANG, TRANSLATIONS["ru"])
    return lang_dict.get(key, TRANSLATIONS["ru"].get(key, key))


def find_app_icon_path() -> str:
    candidates = [
        os.path.join(BUNDLED_ICONS_DIR, "Favorite.png"),
        os.path.join(USER_ICONS_DIR, "Favorite.png"),
        os.path.join(BASE_DIR, "Favorite.png"),
        os.path.join(BUNDLED_ICONS_DIR, "favorite.png"),
        os.path.join(BASE_DIR, "app_icon.ico"),
        os.path.join(BUNDLED_ICONS_DIR, "app_icon.png"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return ""


# Локальные темы папок
THEMES = {
    "Тёмное стекло (Win 11)": ("#2B2D38", "#1E1F26", "#60CDFF", "theme_win11"),
    "Глубокий океан": ("#1A365D", "#0F203C", "#63B3ED", "theme_ocean"),
    "Неоновый фиолет": ("#322659", "#1E1638", "#B794F4", "theme_violet"),
    "Изумрудный лес": ("#1C4532", "#102A1E", "#68D391", "theme_forest"),
    "Тёплый графит": ("#37353E", "#222126", "#F6AD55", "theme_graphite"),
    "Малиновый закат": ("#521B41", "#301026", "#F687B3", "theme_sunset"),
    "Золотое Избранное": ("#423718", "#26200E", "#F6E05E", "theme_gold"),
    "Светлый минимализм": ("#E2E8F0", "#CBD5E1", "#2563EB", "theme_light"),
    "Киберпанк Неон": ("#1A103C", "#0D0722", "#00F5D4", "theme_cyber"),
}

# Глобальные цветовые темы (меняют сразу цвет панели, рамки, всплывающего окна и папок!)
BUILTIN_GLOBAL_THEMES = {
    "Тёмное стекло (Win 11)": {
        "tr_key": "theme_win11",
        "dock_bg_color": "#12131A",
        "dock_border_color": "#FFFFFF",
        "popup_bg_color": "#181922",
        "folder_bg_color": "#2B2D38",
        "folder_accent_color": "#60CDFF",
        "folder_theme": "Тёмное стекло (Win 11)"
    },
    "Глубокий океан": {
        "tr_key": "theme_ocean",
        "dock_bg_color": "#0A1526",
        "dock_border_color": "#63B3ED",
        "popup_bg_color": "#0F1E36",
        "folder_bg_color": "#1A365D",
        "folder_accent_color": "#63B3ED",
        "folder_theme": "Глубокий океан"
    },
    "Неоновый фиолет": {
        "tr_key": "theme_violet",
        "dock_bg_color": "#140E26",
        "dock_border_color": "#B794F4",
        "popup_bg_color": "#1B1333",
        "folder_bg_color": "#322659",
        "folder_accent_color": "#B794F4",
        "folder_theme": "Неоновый фиолет"
    },
    "Изумрудный лес": {
        "tr_key": "theme_forest",
        "dock_bg_color": "#0B1D15",
        "dock_border_color": "#68D391",
        "popup_bg_color": "#10281D",
        "folder_bg_color": "#1C4532",
        "folder_accent_color": "#68D391",
        "folder_theme": "Изумрудный лес"
    },
    "Тёплый графит": {
        "tr_key": "theme_graphite",
        "dock_bg_color": "#18171C",
        "dock_border_color": "#F6AD55",
        "popup_bg_color": "#222126",
        "folder_bg_color": "#37353E",
        "folder_accent_color": "#F6AD55",
        "folder_theme": "Тёплый графит"
    },
    "Малиновый закат": {
        "tr_key": "theme_sunset",
        "dock_bg_color": "#220A1B",
        "dock_border_color": "#F687B3",
        "popup_bg_color": "#2E0E24",
        "folder_bg_color": "#521B41",
        "folder_accent_color": "#F687B3",
        "folder_theme": "Малиновый закат"
    },
    "Светлый минимализм": {
        "tr_key": "theme_light",
        "dock_bg_color": "#F1F5F9",
        "dock_border_color": "#64748B",
        "popup_bg_color": "#F8FAFC",
        "folder_bg_color": "#E2E8F0",
        "folder_accent_color": "#2563EB",
        "folder_theme": "Светлый минимализм"
    },
    "Киберпанк Неон": {
        "tr_key": "theme_cyber",
        "dock_bg_color": "#090414",
        "dock_border_color": "#00F5D4",
        "popup_bg_color": "#120826",
        "folder_bg_color": "#1A103C",
        "folder_accent_color": "#00F5D4",
        "folder_theme": "Киберпанк Неон"
    }
}

DOCK_SHAPES = {
    "rounded": "shape_rounded",
    "hexagon": "shape_hexagon",
    "trapezoid_up": "shape_trap_up",
    "trapezoid_down": "shape_trap_down",
    "chamfer": "shape_chamfer",
    "rect": "shape_rect"
}

ANIMATION_STYLES = {
    "wave": "anim_wave",
    "float_up": "anim_float",
    "spring": "anim_spring",
    "pulse": "anim_pulse",
    "zoom_only": "anim_zoom",
    "tilt": "anim_tilt",
    "none": "anim_none"
}

HOTKEY_PRESETS = {
    "alt_space": (0x0001, 0x20, "hk_alt_space"),
    "ctrl_tilde": (0x0002, 0xC0, "hk_ctrl_tilde"),
    "alt_tilde": (0x0001, 0xC0, "hk_alt_tilde"),
    "alt_q": (0x0001, 0x51, "hk_alt_q"),
    "ctrl_shift_d": (0x0002 | 0x0004, 0x44, "hk_ctrl_shift_d"),
    "win_z": (0x0008, 0x5A, "hk_win_z"),
    "f10": (0x0000, 0x79, "hk_f10"),
    "none": (0, 0, "hk_none")
}



_MENU_ICON_CACHE = {}


def is_color_light(hex_color: str) -> bool:
    """Определяет, светлый ли фон, чтобы автоматически выбрать темные или светлые иконки и текст"""
    c = QColor(hex_color)
    luminance = 0.299 * c.red() + 0.587 * c.green() + 0.114 * c.blue()
    return luminance > 155


def get_menu_stylesheet(bg_hex: str, accent_hex: str = "#60CDFF") -> str:
    """Генерирует стиль контекстного меню (адаптивный под темную и светлую тему)"""
    light = is_color_light(bg_hex)
    text_col = "#1E293B" if light else "#F0F2F5"
    border_col = "#CBD5E1" if light else "#3E4251"
    sep_col = "rgba(0,0,0,25)" if light else "rgba(255,255,255,22)"
    sel_bg = accent_hex if not light else "#2563EB"
    sel_txt = "#111111" if (not light and is_color_light(sel_bg)) else "#FFFFFF"

    return f"""
        QMenu {{
            background-color: {bg_hex}; color: {text_col};
            border: 1px solid {border_col}; border-radius: 9px;
            padding: 6px; font-family: 'Segoe UI'; font-size: 12px;
        }}
        QMenu::item {{ padding: 6px 22px 6px 10px; border-radius: 5px; }}
        QMenu::item:selected {{ background-color: {sel_bg}; color: {sel_txt}; font-weight: 600; }}
        QMenu::icon {{ padding-left: 6px; }}
        QMenu::separator {{ height: 1px; background: {sep_col}; margin: 4px 8px; }}
    """


def get_menu_icon(kind: str, bg_hex: str = "#1F212B") -> QIcon:
    """
    Рисует аккуратные монохромные векторные иконки в едином стиле со скриншотом.
    Автоматически выбирает белый/светло-голубой цвет на темном фоне и темно-графитовый на светлом!
    """
    light_bg = is_color_light(bg_hex)
    fg_hex = "#1E293B" if light_bg else "#E2E8F0"
    cache_k = (kind, fg_hex)
    if cache_k in _MENU_ICON_CACHE:
        return _MENU_ICON_CACHE[cache_k]

    sz = 18
    pix = QPixmap(sz, sz)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    col = QColor(fg_hex)
    pen = QPen(col, 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)

    if kind == "icon_pic":
        p.drawRoundedRect(QRectF(2.5, 3.5, 13, 11), 2.5, 2.5)
        p.drawEllipse(QPointF(6.5, 7.0), 1.3, 1.3)
        p.drawPolyline(QPolygonF([QPointF(3.5, 13), QPointF(7.5, 9.5), QPointF(10.5, 12), QPointF(12.5, 10), QPointF(14.5, 13)]))
    elif kind == "add_app":
        p.drawRoundedRect(QRectF(3, 3, 12, 12), 2.5, 2.5)
        p.drawLine(QPointF(9, 6), QPointF(9, 12))
        p.drawLine(QPointF(6, 9), QPointF(12, 9))
    elif kind == "add_folder":
        p.drawRoundedRect(QRectF(2, 5, 14, 10), 2, 2)
        p.drawLine(QPointF(3, 5), QPointF(7, 5))
        p.drawLine(QPointF(9, 7.5), QPointF(9, 12.5))
        p.drawLine(QPointF(6.5, 10), QPointF(11.5, 10))
    elif kind == "web":
        p.drawEllipse(QRectF(2.5, 2.5, 13, 13))
        p.drawEllipse(QRectF(6, 2.5, 6, 13))
        p.drawLine(QPointF(3, 9), QPointF(15, 9))
    elif kind == "rename":
        p.drawPolygon(QPolygonF([QPointF(12.5, 3), QPointF(15, 5.5), QPointF(6.5, 14), QPointF(3, 15), QPointF(4, 11.5)]))
    elif kind == "rescan":
        p.drawArc(QRectF(3, 3, 12, 12), 30 * 16, 290 * 16)
        p.drawPolyline(QPolygonF([QPointF(11.5, 2.5), QPointF(14.5, 4.5), QPointF(12, 7)]))
    elif kind == "center":
        p.drawEllipse(QRectF(4, 4, 10, 10))
        p.drawLine(QPointF(9, 1.5), QPointF(9, 5))
        p.drawLine(QPointF(9, 13), QPointF(9, 16.5))
        p.drawLine(QPointF(1.5, 9), QPointF(5, 9))
        p.drawLine(QPointF(13, 9), QPointF(16.5, 9))
    elif kind == "edit_move":
        p.drawLine(QPointF(9, 2), QPointF(9, 16))
        p.drawLine(QPointF(2, 9), QPointF(16, 9))
        p.drawPolyline(QPolygonF([QPointF(6.5, 4.5), QPointF(9, 2), QPointF(11.5, 4.5)]))
        p.drawPolyline(QPolygonF([QPointF(6.5, 13.5), QPointF(9, 16), QPointF(11.5, 13.5)]))
    elif kind == "settings":
        p.drawEllipse(QPointF(9, 9), 3.2, 3.2)
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            p.drawLine(
                QPointF(9 + 4.5 * math.cos(rad), 9 + 4.5 * math.sin(rad)),
                QPointF(9 + 6.8 * math.cos(rad), 9 + 6.8 * math.sin(rad))
            )
    elif kind == "about":
        p.drawEllipse(QRectF(2.5, 2.5, 13, 13))
        p.drawLine(QPointF(9, 8.5), QPointF(9, 12.5))
        p.drawPoint(QPointF(9, 5.8))
    elif kind == "delete":
        p.setPen(QPen(QColor("#EF4444" if light_bg else "#F87171"), 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(QPointF(3.5, 5), QPointF(14.5, 5))
        p.drawRoundedRect(QRectF(5, 5, 8, 10.5), 1.5, 1.5)
        p.drawLine(QPointF(7, 3), QPointF(11, 3))
    elif kind == "quit":
        p.setPen(QPen(QColor("#EF4444" if light_bg else "#F87171"), 1.7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawArc(QRectF(3.5, 4, 11, 11), 130 * 16, 280 * 16)
        p.drawLine(QPointF(9, 2.5), QPointF(9, 8.5))
    elif kind == "admin":
        p.drawPolygon(QPolygonF([QPointF(9, 2.5), QPointF(14.5, 5), QPointF(13.5, 11.5), QPointF(9, 15.5), QPointF(4.5, 11.5), QPointF(3.5, 5)]))
    elif kind == "send_folder":
        p.drawLine(QPointF(3, 9), QPointF(14, 9))
        p.drawPolyline(QPolygonF([QPointF(10, 5), QPointF(14.5, 9), QPointF(10, 13)]))
    elif kind == "divider":
        p.drawLine(QPointF(2, 9), QPointF(16, 9))
        p.drawLine(QPointF(6, 6), QPointF(12, 6))
        p.drawLine(QPointF(6, 12), QPointF(12, 12))
    elif kind == "sort":
        p.drawLine(QPointF(5, 3.5), QPointF(5, 14.5))
        p.drawPolyline(QPolygonF([QPointF(2.5, 11.5), QPointF(5, 14.5), QPointF(7.5, 11.5)]))
        p.drawLine(QPointF(10, 5), QPointF(15, 5))
        p.drawLine(QPointF(10, 9), QPointF(13.5, 9))
        p.drawLine(QPointF(10, 13), QPointF(12, 13))
    elif kind == "up":
        p.drawLine(QPointF(9, 15), QPointF(9, 3.5))
        p.drawPolyline(QPolygonF([QPointF(5, 7.5), QPointF(9, 3.5), QPointF(13, 7.5)]))
    elif kind == "down":
        p.drawLine(QPointF(9, 3), QPointF(9, 14.5))
        p.drawPolyline(QPolygonF([QPointF(5, 10.5), QPointF(9, 14.5), QPointF(13, 10.5)]))

    p.end()
    ic = QIcon(pix)
    _MENU_ICON_CACHE[cache_k] = ic
    return ic


_ICON_CACHE = {}
_FOLDER_MASTER_CACHE = {}
_TARGET_CACHE = {}
_FIXED_PATH_CACHE = {}
_SHORTCUT_INDEX = None
_APP_PATHS_INDEX = None
_QT_ICON_PROVIDER = None
_DEFAULT_WEB_ICON = None


def clear_all_caches(clear_disk_cache=False):
    global _ICON_CACHE, _FOLDER_MASTER_CACHE, _TARGET_CACHE, _FIXED_PATH_CACHE, _SHORTCUT_INDEX, _APP_PATHS_INDEX
    _ICON_CACHE.clear()
    _FOLDER_MASTER_CACHE.clear()
    _TARGET_CACHE.clear()
    _FIXED_PATH_CACHE.clear()
    _SHORTCUT_INDEX = None
    _APP_PATHS_INDEX = None
    if clear_disk_cache and os.path.isdir(DISK_ICON_CACHE_DIR):
        try:
            for fn in os.listdir(DISK_ICON_CACHE_DIR):
                if fn.endswith(".png"):
                    os.remove(os.path.join(DISK_ICON_CACHE_DIR, fn))
        except Exception:
            pass


def get_disk_cache_png_path(cache_key: str) -> str:
    digest = hashlib.md5(cache_key.encode("utf-8", errors="ignore")).hexdigest()
    return os.path.join(DISK_ICON_CACHE_DIR, f"ic_{digest}.png")


def is_web_url(path_str: str) -> bool:
    if not path_str:
        return False
    low = path_str.strip().lower()
    return low.startswith(("http://", "https://"))


def normalize_web_url(raw_url: str) -> str:
    u = raw_url.strip()
    if not u:
        return ""
    if not u.lower().startswith(("http://", "https://")):
        u = "http://" + u
    return u


def get_default_web_icon() -> QIcon:
    global _DEFAULT_WEB_ICON
    if _DEFAULT_WEB_ICON is not None:
        return _DEFAULT_WEB_ICON

    pix = QPixmap(48, 48)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    grad = QLinearGradient(6, 6, 42, 42)
    grad.setColorAt(0, QColor("#38BDF8"))
    grad.setColorAt(1, QColor("#2563EB"))
    painter.setBrush(grad)
    painter.setPen(QPen(QColor("#93C5FD"), 1.5))
    painter.drawEllipse(QRectF(6, 6, 36, 36))

    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(QPen(QColor(255, 255, 255, 190), 1.4))
    painter.drawEllipse(QRectF(15, 6, 18, 36))
    painter.drawLine(7, 24, 41, 24)
    painter.drawLine(10, 15, 38, 15)
    painter.drawLine(10, 33, 38, 33)
    painter.end()

    _DEFAULT_WEB_ICON = QIcon(pix)
    return _DEFAULT_WEB_ICON


class FaviconDownloaderThread(QThread):
    favicon_ready = pyqtSignal(str, str)

    def __init__(self, url: str, save_path: str):
        super().__init__()
        self.url = url
        self.save_path = save_path

    def run(self):
        try:
            parsed = urllib.parse.urlparse(self.url)
            host = parsed.hostname or ""
            if not host:
                return
            urls_to_try = [
                f"{parsed.scheme}://{parsed.netloc}/favicon.ico",
                f"https://www.google.com/s2/favicons?domain={host}&sz=64"
            ]
            for fav_url in urls_to_try:
                try:
                    req = urllib.request.Request(fav_url, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=2.5) as resp:
                        data = resp.read()
                        if data and len(data) > 60:
                            qimg = QImage.fromData(data)
                            if not qimg.isNull():
                                qimg.save(self.save_path, "PNG")
                                self.favicon_ready.emit(self.url, self.save_path)
                                return
                except Exception:
                    continue
        except Exception:
            pass


def get_master_folder_pixmap(img_path: str) -> QPixmap:
    if img_path in _FOLDER_MASTER_CACHE:
        return _FOLDER_MASTER_CACHE[img_path]
    pix = QPixmap(img_path)
    if not pix.isNull() and (pix.width() > 160 or pix.height() > 160):
        pix = pix.scaled(160, 160, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    _FOLDER_MASTER_CACHE[img_path] = pix
    return pix


def get_qt_provider():
    global _QT_ICON_PROVIDER
    if _QT_ICON_PROVIDER is None:
        _QT_ICON_PROVIDER = QFileIconProvider()
    return _QT_ICON_PROVIDER


def get_tile_colors(folder_data):
    is_fav = folder_data.get("is_favorites", False)
    default_theme = "Золотое Избранное" if is_fav else "Тёмное стекло (Win 11)"
    theme_name = folder_data.get("theme", default_theme)

    if theme_name in ("Свой цвет", "Custom Color", "Свой цвет (Вручную)") or folder_data.get("custom_bg_color"):
        c_bg = QColor(folder_data.get("custom_bg_color", "#2B2D38"))
        c1_hex = c_bg.lighter(112).name()
        c2_hex = c_bg.darker(118).name()
        accent_hex = folder_data.get("custom_accent_color", "#60CDFF")
        return c1_hex, c2_hex, accent_hex

    c1_hex, c2_hex, accent_hex, _ = THEMES.get(theme_name, THEMES["Тёмное стекло (Win 11)"])
    if folder_data.get("custom_accent_color"):
        accent_hex = folder_data["custom_accent_color"]
    return c1_hex, c2_hex, accent_hex


def build_rounded_polygon_path(points: list[QPointF], radius: float) -> QPainterPath:
    path = QPainterPath()
    n = len(points)
    if n < 3:
        return path

    if radius <= 0.5:
        for i, pt in enumerate(points):
            if i == 0:
                path.moveTo(pt)
            else:
                path.lineTo(pt)
        path.closeSubpath()
        return path

    for i in range(n):
        p_prev = points[(i - 1) % n]
        p_curr = points[i]
        p_next = points[(i + 1) % n]

        v1_x, v1_y = p_prev.x() - p_curr.x(), p_prev.y() - p_curr.y()
        v2_x, v2_y = p_next.x() - p_curr.x(), p_next.y() - p_curr.y()

        len1 = math.hypot(v1_x, v1_y)
        len2 = math.hypot(v2_x, v2_y)

        if len1 < 1e-4 or len2 < 1e-4:
            continue

        r = min(radius, len1 * 0.45, len2 * 0.45)

        start_pt = QPointF(p_curr.x() + (v1_x / len1) * r, p_curr.y() + (v1_y / len1) * r)
        end_pt = QPointF(p_curr.x() + (v2_x / len2) * r, p_curr.y() + (v2_y / len2) * r)

        if i == 0:
            path.moveTo(start_pt)
        else:
            path.lineTo(start_pt)

        path.quadTo(p_curr, end_pt)

    path.closeSubpath()
    return path


kernel32 = ctypes.windll.kernel32
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
shell32 = ctypes.windll.shell32
ole32 = ctypes.windll.ole32

HOTKEY_ID = 9001
WM_HOTKEY = 0x0312
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", wintypes.POINT),
    ]


class HotkeyEventFilter(QAbstractNativeEventFilter):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def nativeEventFilter(self, eventType, message):
        if eventType == b"windows_generic_MSG":
            try:
                msg = MSG.from_address(int(message))
                if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                    QTimer.singleShot(0, self.callback)
                    return True, 0
            except Exception:
                pass
        return False, 0


def set_window_topmost_win32(widget: QWidget, is_topmost: bool):
    if not widget:
        return
    try:
        hwnd = int(widget.winId())
        z_order = HWND_TOPMOST if is_topmost else HWND_NOTOPMOST
        user32.SetWindowPos(
            wintypes.HWND(hwnd),
            wintypes.HWND(z_order),
            0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW
        )
    except Exception:
        pass


class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.c_size_t),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", wintypes.LONG),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", wintypes.WCHAR * 260),
    ]


kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
kernel32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
kernel32.Process32FirstW.restype = wintypes.BOOL
kernel32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
kernel32.Process32NextW.restype = wintypes.BOOL
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL


def is_any_mouse_button_down() -> bool:
    return bool((user32.GetAsyncKeyState(0x01) & 0x8000) or (user32.GetAsyncKeyState(0x02) & 0x8000))


def get_running_process_names_fast() -> set:
    running = set()
    TH32CS_SNAPPROCESS = 0x00000002
    h_snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if h_snap == wintypes.HANDLE(-1).value or not h_snap:
        return running
    try:
        pe = PROCESSENTRY32W()
        pe.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        if kernel32.Process32FirstW(h_snap, ctypes.byref(pe)):
            while True:
                running.add(pe.szExeFile.lower())
                if not kernel32.Process32NextW(h_snap, ctypes.byref(pe)):
                    break
    finally:
        kernel32.CloseHandle(h_snap)
    return running


class ProcessMonitorThread(QThread):
    processes_updated = pyqtSignal(set)

    def run(self):
        procs = get_running_process_names_fast()
        self.processes_updated.emit(procs)


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


class SHFILEINFOW(ctypes.Structure):
    _fields_ = [
        ("hIcon", wintypes.HANDLE),
        ("iIcon", ctypes.c_int),
        ("dwAttributes", wintypes.DWORD),
        ("szDisplayName", wintypes.WCHAR * 260),
        ("szTypeName", wintypes.WCHAR * 80),
    ]


user32.GetDC.argtypes = [wintypes.HWND]
user32.GetDC.restype = wintypes.HDC
user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
user32.ReleaseDC.restype = ctypes.c_int
user32.DrawIconEx.argtypes = [
    wintypes.HDC, ctypes.c_int, ctypes.c_int, wintypes.HANDLE,
    ctypes.c_int, ctypes.c_int, wintypes.UINT, wintypes.HBRUSH, wintypes.UINT
]
user32.DrawIconEx.restype = wintypes.BOOL
user32.DestroyIcon.argtypes = [wintypes.HANDLE]
user32.DestroyIcon.restype = wintypes.BOOL

gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
gdi32.CreateCompatibleDC.restype = wintypes.HDC
gdi32.CreateCompatibleBitmap.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
gdi32.CreateCompatibleBitmap.restype = wintypes.HBITMAP
gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HANDLE]
gdi32.SelectObject.restype = wintypes.HANDLE
gdi32.DeleteObject.argtypes = [wintypes.HANDLE]
gdi32.DeleteObject.restype = wintypes.BOOL
gdi32.DeleteDC.argtypes = [wintypes.HDC]
gdi32.DeleteDC.restype = wintypes.BOOL
gdi32.GetDIBits.argtypes = [
    wintypes.HDC, wintypes.HBITMAP, wintypes.UINT, wintypes.UINT,
    ctypes.c_void_p, ctypes.POINTER(BITMAPINFOHEADER), wintypes.UINT
]
gdi32.GetDIBits.restype = ctypes.c_int

shell32.SHGetFileInfoW.argtypes = [
    ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(SHFILEINFOW),
    wintypes.UINT, wintypes.UINT
]
shell32.SHGetFileInfoW.restype = ctypes.c_size_t
shell32.ILCreateFromPathW.argtypes = [wintypes.LPCWSTR]
shell32.ILCreateFromPathW.restype = ctypes.c_void_p
shell32.ILFree.argtypes = [ctypes.c_void_p]
shell32.ILFree.restype = None
shell32.ExtractIconExW.argtypes = [
    wintypes.LPCWSTR, ctypes.c_int,
    ctypes.POINTER(wintypes.HANDLE), ctypes.POINTER(wintypes.HANDLE), wintypes.UINT
]
shell32.ExtractIconExW.restype = wintypes.UINT


def hicon_to_qimage(hicon, size=48):
    if not hicon:
        return None
    hdc_screen = user32.GetDC(None)
    hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
    hbmp = gdi32.CreateCompatibleBitmap(hdc_screen, size, size)
    old_obj = gdi32.SelectObject(hdc_mem, hbmp)

    user32.DrawIconEx(hdc_mem, 0, 0, hicon, size, size, 0, None, 3)

    bmi = BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.biWidth = size
    bmi.biHeight = -size
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    bmi.biCompression = 0

    buf_size = size * size * 4
    pixel_buf = (ctypes.c_ubyte * buf_size)()
    lines = gdi32.GetDIBits(hdc_mem, hbmp, 0, size, pixel_buf, ctypes.byref(bmi), 0)

    gdi32.SelectObject(hdc_mem, old_obj)
    gdi32.DeleteObject(hbmp)
    gdi32.DeleteDC(hdc_mem)
    user32.ReleaseDC(None, hdc_screen)

    if not lines:
        return None

    raw = bytearray(pixel_buf)
    has_alpha = any(raw[i] != 0 for i in range(3, buf_size, 4))
    has_color = any(raw[i] != 0 for i in range(0, buf_size))

    if not has_alpha and not has_color:
        return None
    if not has_alpha and has_color:
        for i in range(3, buf_size, 4):
            raw[i] = 255

    return QImage(bytes(raw), size, size, QImage.Format.Format_ARGB32).copy()


def hicon_to_qicon(hicon, size=48):
    qimg = hicon_to_qimage(hicon, size)
    if qimg is None or qimg.isNull():
        return None
    pix = QPixmap.fromImage(qimg)
    return QIcon(pix) if not pix.isNull() else None


def build_app_paths_registry_index() -> dict:
    global _APP_PATHS_INDEX
    if _APP_PATHS_INDEX is not None:
        return _APP_PATHS_INDEX

    _APP_PATHS_INDEX = {}
    reg_roots = [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]
    subkey_path = r"Software\Microsoft\Windows\CurrentVersion\App Paths"

    for root in reg_roots:
        try:
            key = winreg.OpenKey(root, subkey_path, 0, winreg.KEY_READ)
            i = 0
            while True:
                try:
                    exe_sub = winreg.EnumKey(key, i)
                    i += 1
                    try:
                        sub_k = winreg.OpenKey(key, exe_sub, 0, winreg.KEY_READ)
                        val, _ = winreg.QueryValueEx(sub_k, "")
                        winreg.CloseKey(sub_k)
                        if val and isinstance(val, str):
                            clean_p = os.path.normpath(os.path.expandvars(val.strip('" ')))
                            if os.path.exists(clean_p):
                                _APP_PATHS_INDEX[exe_sub.lower()] = clean_p
                                base_no_ext = os.path.splitext(exe_sub)[0].lower()
                                _APP_PATHS_INDEX[base_no_ext] = clean_p
                    except Exception:
                        pass
                except OSError:
                    break
            winreg.CloseKey(key)
        except Exception:
            pass
    return _APP_PATHS_INDEX


def build_shortcut_index():
    global _SHORTCUT_INDEX
    if _SHORTCUT_INDEX is not None:
        return _SHORTCUT_INDEX

    _SHORTCUT_INDEX = {}
    search_roots = [
        os.path.expanduser("~\\Desktop"),
        os.path.join(os.environ.get("PUBLIC", "C:\\Users\\Public"), "Desktop"),
        os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs"),
        os.path.join(os.environ.get("PROGRAMDATA", "C:\\ProgramData"), r"Microsoft\Windows\Start Menu\Programs"),
    ]
    for root_dir in search_roots:
        if not root_dir or not os.path.isdir(root_dir):
            continue
        for dirpath, _, filenames in os.walk(root_dir):
            for fn in filenames:
                if fn.lower().endswith((".lnk", ".url")):
                    base = os.path.splitext(fn)[0].lower()
                    clean = base.replace(" — ярлык", "").replace(" - ярлык", "").replace(" - shortcut", "").strip()
                    full_p = os.path.join(dirpath, fn)
                    if clean not in _SHORTCUT_INDEX:
                        _SHORTCUT_INDEX[clean] = full_p
                    if base not in _SHORTCUT_INDEX:
                        _SHORTCUT_INDEX[base] = full_p
    return _SHORTCUT_INDEX


def try_relocate_missing_path(raw_path: str) -> str:
    if not raw_path:
        return ""
    expanded = os.path.normpath(os.path.expandvars(raw_path.strip('" ')))
    if expanded.startswith("\\\\") or os.path.exists(expanded):
        return expanded

    current_user_dir = os.path.expanduser("~")
    user_match = re.match(r"^[A-Za-z]:\\Users\\[^\\]+\\(.*)$", expanded, re.IGNORECASE)
    if user_match:
        rel_inside_user = user_match.group(1)
        cand_user = os.path.join(current_user_dir, rel_inside_user)
        if os.path.exists(cand_user):
            return cand_user

    if len(expanded) > 3 and expanded[1:3] == ":\\":
        for drv in ("C", "D", "E", "F"):
            cand_drv = f"{drv}:{expanded[2:]}"
            if os.path.exists(cand_drv):
                return cand_drv
            if user_match:
                cand_drv_user = f"{drv}:\\Users\\{os.path.basename(current_user_dir)}\\{user_match.group(1)}"
                if os.path.exists(cand_drv_user):
                    return cand_drv_user

    fname_low = os.path.basename(expanded).lower()
    if fname_low.endswith(".exe"):
        app_paths = build_app_paths_registry_index()
        if fname_low in app_paths:
            return app_paths[fname_low]

    return expanded


def smart_fix_path(path_str, app_name="", allow_heavy_scan=True):
    if not path_str:
        return ""
    if is_web_url(path_str):
        return path_str.strip()

    cache_k = (path_str, app_name)
    if cache_k in _FIXED_PATH_CACHE:
        return _FIXED_PATH_CACHE[cache_k]

    relocated = try_relocate_missing_path(path_str)
    if relocated.startswith("\\\\") or os.path.exists(relocated):
        _FIXED_PATH_CACHE[cache_k] = relocated
        return relocated

    fname = os.path.basename(relocated)
    current_user_dir = os.path.expanduser("~")
    for d in (
        os.path.join(current_user_dir, "Desktop"),
        os.path.join(os.environ.get("PUBLIC", "C:\\Users\\Public"), "Desktop")
    ):
        if os.path.isdir(d):
            cand = os.path.join(d, fname)
            if os.path.exists(cand):
                _FIXED_PATH_CACHE[cache_k] = cand
                return cand
            if not fname.lower().endswith(".lnk"):
                cand_lnk = cand + ".lnk"
                if os.path.exists(cand_lnk):
                    _FIXED_PATH_CACHE[cache_k] = cand_lnk
                    return cand_lnk

    if not allow_heavy_scan:
        return relocated

    idx_map = build_shortcut_index()
    clean_title = (
        (app_name or os.path.splitext(fname)[0])
        .lower()
        .replace(" — ярлык", "")
        .replace(" - ярлык", "")
        .replace(" - shortcut", "")
        .strip()
    )

    if clean_title in idx_map and os.path.exists(idx_map[clean_title]):
        res = idx_map[clean_title]
        _FIXED_PATH_CACHE[cache_k] = res
        return res

    base_f = os.path.splitext(fname)[0].lower()
    if base_f in idx_map and os.path.exists(idx_map[base_f]):
        res = idx_map[base_f]
        _FIXED_PATH_CACHE[cache_k] = res
        return res

    app_paths = build_app_paths_registry_index()
    if clean_title in app_paths:
        res = app_paths[clean_title]
        _FIXED_PATH_CACHE[cache_k] = res
        return res

    _FIXED_PATH_CACHE[cache_k] = relocated
    return relocated


def extract_paths_from_lnk_binary(lnk_path):
    found = []
    try:
        with open(lnk_path, "rb") as f:
            data = f.read()

        pattern = r'(?:[A-Za-z]:\\|%[A-Za-z0-9_()]+%\\)[^\x00"<>|?*]+?\.(?:exe|ico|dll)'

        for encoding in ("utf-16-le", "cp1251"):
            decoded = data.decode(encoding, errors="ignore")
            for match in re.finditer(pattern, decoded, re.IGNORECASE):
                raw_p = match.group(0)
                relocated = try_relocate_missing_path(raw_p)
                if relocated and not relocated.startswith("\\\\") and os.path.exists(relocated):
                    if relocated not in found:
                        found.append(relocated)
    except Exception:
        pass
    return found


def resolve_shortcut_target(path_str, app_name="", allow_heavy_scan=True):
    if not path_str or is_web_url(path_str):
        return path_str
    cache_key = (path_str, app_name)
    if cache_key in _TARGET_CACHE:
        return _TARGET_CACHE[cache_key]

    fixed = smart_fix_path(path_str, app_name, allow_heavy_scan=allow_heavy_scan)
    if not fixed or fixed.startswith("\\\\") or is_web_url(fixed):
        _TARGET_CACHE[cache_key] = fixed
        return fixed

    low = fixed.lower()
    result = fixed
    if low.endswith(".lnk") and os.path.exists(fixed):
        info = QFileInfo(fixed)
        qt_target = info.symLinkTarget()
        if qt_target:
            qt_reloc = try_relocate_missing_path(qt_target)
            if os.path.exists(qt_reloc):
                _TARGET_CACHE[cache_key] = qt_reloc
                return qt_reloc

        paths = extract_paths_from_lnk_binary(fixed)
        exe_found = next((p for p in paths if p.lower().endswith(".exe")), None)
        if exe_found:
            result = exe_found
        elif paths:
            result = paths[0]
    elif low.endswith(".url") and os.path.exists(fixed):
        try:
            with open(fixed, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if line.strip().lower().startswith("iconfile="):
                        ic_p = line.strip().split("=", 1)[1].strip()
                        reloc_ic = try_relocate_missing_path(ic_p)
                        if not reloc_ic.startswith("\\\\") and os.path.exists(reloc_ic):
                            result = reloc_ic
                            break
        except Exception:
            pass

    _TARGET_CACHE[cache_key] = result
    return result


def get_accurate_file_icon(app_data):
    if app_data.get("is_separator"):
        return QIcon()

    custom_ic = app_data.get("custom_icon", "")
    raw_path = app_data.get("path", "")
    app_name = app_data.get("name", "")

    fast_cache_key = f"{custom_ic}|{raw_path}|{app_name}"
    if fast_cache_key in _ICON_CACHE:
        return _ICON_CACHE[fast_cache_key]

    if custom_ic:
        resolved_custom = resolve_image_path(custom_ic)
        if resolved_custom and os.path.exists(resolved_custom):
            ic = QIcon(resolved_custom)
            _ICON_CACHE[fast_cache_key] = ic
            return ic

    if is_web_url(raw_path) or app_data.get("is_web"):
        ic = get_default_web_icon()
        _ICON_CACHE[fast_cache_key] = ic
        return ic

    disk_png = get_disk_cache_png_path(fast_cache_key)
    if os.path.exists(disk_png):
        pix = QPixmap(disk_png)
        if not pix.isNull():
            ic = QIcon(pix)
            _ICON_CACHE[fast_cache_key] = ic
            return ic

    norm_path = smart_fix_path(raw_path, app_name, allow_heavy_scan=False)
    if norm_path and norm_path != raw_path and not norm_path.startswith("\\\\") and os.path.exists(norm_path):
        app_data["path"] = norm_path

    if not norm_path:
        ic = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
        _ICON_CACHE[fast_cache_key] = ic
        return ic

    if norm_path.startswith("\\\\"):
        ic = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DriveNetIcon)
        _ICON_CACHE[fast_cache_key] = ic
        return ic

    def save_and_cache(qic: QIcon) -> QIcon:
        _ICON_CACHE[fast_cache_key] = qic
        try:
            p = qic.pixmap(QSize(48, 48))
            if not p.isNull():
                p.save(disk_png, "PNG")
        except Exception:
            pass
        return qic

    if os.path.isdir(norm_path):
        pidl = shell32.ILCreateFromPathW(norm_path)
        if pidl:
            shfi = SHFILEINFOW()
            res = shell32.SHGetFileInfoW(pidl, 0, ctypes.byref(shfi), ctypes.sizeof(shfi), 0x108)
            shell32.ILFree(pidl)
            if res and shfi.hIcon:
                qic = hicon_to_qicon(shfi.hIcon, 48)
                user32.DestroyIcon(shfi.hIcon)
                if qic and not qic.isNull():
                    return save_and_cache(qic)
        ic = get_qt_provider().icon(QFileInfo(norm_path))
        if ic.isNull():
            ic = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
        return save_and_cache(ic)

    candidates = []

    def add_cand(p):
        if p:
            reloc = try_relocate_missing_path(p)
            if reloc and not reloc.startswith("\\\\") and os.path.exists(reloc) and reloc not in candidates:
                candidates.append(reloc)

    if os.path.exists(norm_path):
        if norm_path.lower().endswith(".lnk"):
            qt_target = QFileInfo(norm_path).symLinkTarget()
            add_cand(qt_target)
            for p in extract_paths_from_lnk_binary(norm_path):
                add_cand(p)
        add_cand(norm_path)
    else:
        norm_heavy = smart_fix_path(raw_path, app_name, allow_heavy_scan=True)
        if norm_heavy and os.path.exists(norm_heavy):
            if norm_heavy.lower().endswith(".lnk"):
                add_cand(QFileInfo(norm_heavy).symLinkTarget())
                for p in extract_paths_from_lnk_binary(norm_heavy):
                    add_cand(p)
            add_cand(norm_heavy)

    for c in list(candidates):
        if c.lower().endswith(".exe") and os.path.isfile(c):
            app_dir = os.path.dirname(c)
            try:
                for fn in os.listdir(app_dir):
                    if fn.lower().endswith(".ico"):
                        add_cand(os.path.join(app_dir, fn))
            except Exception:
                pass

    for cand in candidates:
        if cand.lower().endswith((".exe", ".ico", ".dll")):
            h_large = wintypes.HANDLE()
            h_small = wintypes.HANDLE()
            cnt = shell32.ExtractIconExW(cand, 0, ctypes.byref(h_large), ctypes.byref(h_small), 1)
            if cnt > 0 and h_large.value:
                qic = hicon_to_qicon(h_large.value, 48)
                user32.DestroyIcon(h_large)
                if h_small.value:
                    user32.DestroyIcon(h_small)
                if qic and not qic.isNull():
                    return save_and_cache(qic)

    for cand in candidates:
        pidl = shell32.ILCreateFromPathW(cand)
        if pidl:
            shfi = SHFILEINFOW()
            res = shell32.SHGetFileInfoW(pidl, 0, ctypes.byref(shfi), ctypes.sizeof(shfi), 0x108)
            shell32.ILFree(pidl)
            if res and shfi.hIcon:
                qic = hicon_to_qicon(shfi.hIcon, 48)
                user32.DestroyIcon(shfi.hIcon)
                if qic and not qic.isNull():
                    return save_and_cache(qic)

    for cand in candidates:
        shfi = SHFILEINFOW()
        res = shell32.SHGetFileInfoW(ctypes.c_wchar_p(cand), 0, ctypes.byref(shfi), ctypes.sizeof(shfi), 0x100)
        if res and shfi.hIcon:
            qic = hicon_to_qicon(shfi.hIcon, 48)
            user32.DestroyIcon(shfi.hIcon)
            if qic and not qic.isNull():
                return save_and_cache(qic)

    provider = get_qt_provider()
    for cand in candidates:
        qt_ic = provider.icon(QFileInfo(cand))
        if not qt_ic.isNull():
            return save_and_cache(qt_ic)

    fallback_ic = provider.icon(QFileInfo(norm_path))
    _ICON_CACHE[fast_cache_key] = fallback_ic
    return fallback_ic


class BackgroundWarmerThread(QThread):
    item_warmed = pyqtSignal()
    finished_warming = pyqtSignal(bool)

    def __init__(self, folders_data):
        super().__init__()
        self.folders_data = folders_data

    def run(self):
        try:
            ole32.CoInitialize(None)
        except Exception:
            pass

        config_dirty = False
        for folder in self.folders_data:
            for app_data in folder.get("apps", []):
                if app_data.get("is_separator"):
                    continue
                self.msleep(25)
                raw_p = app_data.get("path", "")
                app_name = app_data.get("name", "")

                if is_web_url(raw_p) or app_data.get("is_web") or app_data.get("is_dir"):
                    if "exe_name" not in app_data:
                        app_data["exe_name"] = ""
                    continue

                if "exe_name" not in app_data:
                    if raw_p.lower().endswith(".exe"):
                        app_data["exe_name"] = os.path.basename(raw_p).lower()
                    elif raw_p.startswith("\\\\"):
                        app_data["exe_name"] = ""
                    else:
                        target = resolve_shortcut_target(raw_p, app_name, allow_heavy_scan=False)
                        app_data["exe_name"] = (
                            os.path.basename(target).lower()
                            if (target and target.lower().endswith(".exe"))
                            else ""
                        )
                    config_dirty = True

                custom_ic = app_data.get("custom_icon", "")
                if not custom_ic and not raw_p.startswith("\\\\"):
                    fast_key = f"{custom_ic}|{raw_p}|{app_name}"
                    disk_png = get_disk_cache_png_path(fast_key)
                    if not os.path.exists(disk_png):
                        target_p = resolve_shortcut_target(raw_p, app_name, allow_heavy_scan=False)
                        for cand in (target_p, raw_p):
                            if cand and os.path.exists(cand):
                                pidl = shell32.ILCreateFromPathW(cand)
                                if pidl:
                                    shfi = SHFILEINFOW()
                                    res = shell32.SHGetFileInfoW(pidl, 0, ctypes.byref(shfi), ctypes.sizeof(shfi), 0x108)
                                    shell32.ILFree(pidl)
                                    if res and shfi.hIcon:
                                        qimg = hicon_to_qimage(shfi.hIcon, 48)
                                        user32.DestroyIcon(shfi.hIcon)
                                        if qimg and not qimg.isNull():
                                            try:
                                                qimg.save(disk_png, "PNG")
                                            except Exception:
                                                pass
                                            break

        self.finished_warming.emit(config_dirty)


def is_app_running(app_data, running_set):
    if not running_set or app_data.get("is_separator"):
        return False
    raw_p = app_data.get("path", "")
    if is_web_url(raw_p) or app_data.get("is_web") or app_data.get("is_dir"):
        return False

    exe_name = app_data.get("exe_name")
    if exe_name is None:
        if raw_p.lower().endswith(".exe"):
            exe_name = os.path.basename(raw_p).lower()
            app_data["exe_name"] = exe_name
        else:
            exe_name = ""

    if exe_name and exe_name in running_set:
        return True
    clean_title = app_data.get("name", "").lower().strip() + ".exe"
    return clean_title in running_set


def launch_as_admin(path_str, app_name=""):
    if is_web_url(path_str):
        webbrowser.open(path_str)
        return
    fixed = smart_fix_path(path_str, app_name)
    target = resolve_shortcut_target(fixed, app_name)
    run_target = target if (target and os.path.exists(target)) else fixed
    work_dir = os.path.dirname(run_target)
    shell32.ShellExecuteW(None, "runas", ctypes.c_wchar_p(run_target), None, ctypes.c_wchar_p(work_dir), 1)


def open_file_location(path_str, app_name=""):
    if is_web_url(path_str):
        webbrowser.open(path_str)
        return
    fixed = smart_fix_path(path_str, app_name)
    target = resolve_shortcut_target(fixed, app_name)
    norm_target = os.path.normpath(target if (target and os.path.exists(target)) else fixed)
    if os.path.isdir(norm_target):
        os.startfile(norm_target)
    else:
        subprocess.Popen(f'explorer /select,"{norm_target}"')


def is_autostart_enabled():
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_READ
        )
        val, _ = winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return bool(val)
    except Exception:
        return False


def set_autostart(enable: bool):
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        if enable:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, EXE_PATH)
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return True
    except Exception:
        return False


def resolve_image_path(path_str):
    if not path_str:
        return ""
    if os.path.isabs(path_str) and os.path.exists(path_str):
        return path_str
    fname = os.path.basename(path_str)
    for folder in (BUNDLED_ICONS_DIR, USER_ICONS_DIR, BASE_DIR, DATA_DIR):
        cand1 = os.path.join(folder, path_str)
        if os.path.exists(cand1):
            return cand1
        cand2 = os.path.join(folder, fname)
        if os.path.exists(cand2):
            return cand2
    return ""


class AboutDialog(QDialog):
    def __init__(self, manager):
        super().__init__(None)
        self.manager = manager
        self.setWindowTitle(tr("about_title"))
        if self.manager.app_icon:
            self.setWindowIcon(self.manager.app_icon)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowCloseButtonHint)
        self.setFixedSize(400, 360)
        self.setStyleSheet("""
            QDialog { background-color: #1A1B23; color: #FFFFFF; font-family: 'Segoe UI'; }
            QLabel { color: #D0D4DC; font-size: 13px; }
            QPushButton#CloudTipsBtn {
                background-color: #2563EB; color: #FFFFFF; border: 1px solid #60A5FA;
                border-radius: 8px; padding: 9px 14px; font-weight: 600; font-size: 13px;
            }
            QPushButton#CloudTipsBtn:hover { background-color: #3B82F6; }
            QPushButton#DonatePayBtn {
                background-color: #D97706; color: #FFFFFF; border: 1px solid #FBBF24;
                border-radius: 8px; padding: 9px 14px; font-weight: 600; font-size: 13px;
            }
            QPushButton#DonatePayBtn:hover { background-color: #F59E0B; }
            QPushButton#GithubBtn {
                background-color: #24292F; color: #FFFFFF; border: 1px solid #57606A;
                border-radius: 8px; padding: 8px 14px; font-weight: 600; font-size: 13px;
            }
            QPushButton#GithubBtn:hover { background-color: #32383F; border-color: #8B949E; }
            QPushButton#CloseBtn {
                background-color: rgba(255, 255, 255, 18); color: #FFFFFF; border: none;
                border-radius: 7px; padding: 7px 22px; font-size: 12px;
            }
            QPushButton#CloseBtn:hover { background-color: rgba(255, 255, 255, 30); }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(8)

        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if self.manager.app_icon:
            icon_lbl.setPixmap(self.manager.app_icon.pixmap(QSize(60, 60)))
        layout.addWidget(icon_lbl)

        title_lbl = QLabel(f"<b style='font-size:17px; color:#FFFFFF;'>{APP_TITLE}</b>")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_lbl)

        ver_lbl = QLabel(f"{tr('version_lbl')} <b>{APP_VERSION}</b>")
        ver_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ver_lbl.setStyleSheet("color: #60CDFF; font-size: 13px;")
        layout.addWidget(ver_lbl)

        desc_lbl = QLabel(tr("about_desc"))
        desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_lbl.setStyleSheet("color: #94A3B8; font-size: 12px;")
        layout.addWidget(desc_lbl)

        layout.addSpacing(4)
        sup_lbl = QLabel(tr("support_header"))
        sup_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sup_lbl.setStyleSheet("color: #E2E8F0; font-size: 12px; font-weight: 600;")
        layout.addWidget(sup_lbl)

        donate_row = QHBoxLayout()
        donate_row.setSpacing(10)

        cloud_btn = QPushButton("CloudTips")
        cloud_btn.setObjectName("CloudTipsBtn")
        cloud_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        cloud_btn.clicked.connect(lambda: webbrowser.open(CLOUDTIPS_URL))
        donate_row.addWidget(cloud_btn)

        dp_btn = QPushButton("DonatePay")
        dp_btn.setObjectName("DonatePayBtn")
        dp_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        dp_btn.clicked.connect(lambda: webbrowser.open(DONATEPAY_URL))
        donate_row.addWidget(dp_btn)

        layout.addLayout(donate_row)

        gh_btn = QPushButton(tr("github_btn"))
        gh_btn.setObjectName("GithubBtn")
        gh_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        gh_btn.clicked.connect(lambda: webbrowser.open(GITHUB_URL))
        layout.addWidget(gh_btn)

        layout.addStretch()

        close_btn = QPushButton(tr("close_btn"))
        close_btn.setObjectName("CloseBtn")
        close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close_btn.clicked.connect(self.accept)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)


class UnifiedSettingsDialog(QDialog):
    def __init__(self, manager, target_tile=None, initial_tab=0):
        super().__init__(None)
        self.manager = manager
        self.settings = manager.settings
        self.target_tile = target_tile or (manager.get_all_tiles()[0] if manager.get_all_tiles() else None)
        self.sample_data = self.target_tile.data if self.target_tile else (manager.folders_data[0] if manager.folders_data else {})

        self.setWindowTitle(f"{tr('settings_win_title')} — {APP_TITLE} v{APP_VERSION}")
        if self.manager.app_icon:
            self.setWindowIcon(self.manager.app_icon)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowCloseButtonHint)
        self.setFixedSize(670, 625)
        self.setStyleSheet("""
            QDialog { background-color: #16171F; color: #FFFFFF; font-family: 'Segoe UI'; }
            QTabWidget::pane {
                border: 1px solid #2D3142; border-radius: 8px;
                background-color: #1E202B; top: -1px;
            }
            QTabBar::tab {
                background-color: #16171F; color: #94A3B8;
                border: 1px solid #2D3142; border-bottom: none;
                border-top-left-radius: 7px; border-top-right-radius: 7px;
                padding: 8px 14px; margin-right: 3px; font-weight: 600; font-size: 12px;
            }
            QTabBar::tab:selected {
                background-color: #1E202B; color: #60CDFF; border-top: 2px solid #60CDFF;
            }
            QLabel { color: #D0D4DC; font-size: 13px; }
            QComboBox, QSpinBox {
                background-color: #262834; color: white; border: 1px solid #3E4251;
                border-radius: 6px; padding: 5px 8px; font-size: 13px;
            }
            QComboBox QAbstractItemView {
                background-color: #262834; color: white; selection-background-color: #3B5998;
            }
            QCheckBox { color: #E2E8F0; font-size: 13px; spacing: 8px; }
            QSlider::groove:horizontal {
                height: 6px; background: #2D3142; border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #60CDFF; width: 16px; height: 16px; margin: -5px 0; border-radius: 8px;
            }
            QPushButton {
                background-color: #2B579A; color: white; border: none;
                border-radius: 7px; padding: 6px 12px; font-weight: 600; font-size: 12px;
            }
            QPushButton:hover { background-color: #3B69B0; }
        """)

        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.timeout.connect(self.manager.save_config)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        self.tabs = QTabWidget()
        self.tabs.tabBar().setUsesScrollButtons(False)
        self.tabs.addTab(self._build_panel_tab(), tr("tab_panel"))
        self.tabs.addTab(self._build_folders_tab(), tr("tab_folders"))
        self.tabs.addTab(self._build_popup_tab(), tr("tab_popup"))
        self.tabs.addTab(self._build_system_tab(), tr("tab_system"))
        self.tabs.addTab(self._build_about_tab(), tr("tab_about"))
        self.tabs.setCurrentIndex(initial_tab)
        main_layout.addWidget(self.tabs, 1)

        bottom_row = QHBoxLayout()
        cfg_info = QLabel(f"{tr('cfg_file_lbl')} {CONFIG_FILE}")
        cfg_info.setStyleSheet("color: #64748B; font-size: 11px;")
        bottom_row.addWidget(cfg_info, 1)

        ok_btn = QPushButton(tr("done_btn"))
        ok_btn.clicked.connect(self.accept)
        bottom_row.addWidget(ok_btn)
        main_layout.addLayout(bottom_row)

    def _populate_global_theme_combo(self):
        self.global_theme_combo.blockSignals(True)
        self.global_theme_combo.clear()
        cur_gt = self.settings.get("global_theme", "Тёмное стекло (Win 11)")

        for k, v in BUILTIN_GLOBAL_THEMES.items():
            self.global_theme_combo.addItem(tr(v["tr_key"]), k)
            if k == cur_gt:
                self.global_theme_combo.setCurrentIndex(self.global_theme_combo.count() - 1)

        custom_themes = self.settings.get("custom_global_themes", {})
        for k in custom_themes.keys():
            self.global_theme_combo.addItem(f"★ {k}", k)
            if k == cur_gt:
                self.global_theme_combo.setCurrentIndex(self.global_theme_combo.count() - 1)

        self.global_theme_combo.addItem(tr("theme_custom"), "__custom__")
        if cur_gt == "__custom__":
            self.global_theme_combo.setCurrentIndex(self.global_theme_combo.count() - 1)

        self.global_theme_combo.blockSignals(False)

    def _build_panel_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 14, 20, 14)
        form = QFormLayout()
        form.setSpacing(10)

        # Выбор глобальной темы + кнопки сохранения своей темы
        theme_row = QHBoxLayout()
        self.global_theme_combo = QComboBox()
        self._populate_global_theme_combo()
        self.global_theme_combo.currentIndexChanged.connect(self.on_global_theme_selected)
        theme_row.addWidget(self.global_theme_combo, 1)

        save_th_btn = QPushButton(tr("btn_save_theme"))
        save_th_btn.clicked.connect(self.save_custom_global_theme)
        theme_row.addWidget(save_th_btn)

        self.mode_combo = QComboBox()
        modes = [
            (tr("mode_h"), "dock_horizontal"),
            (tr("mode_v"), "dock_vertical"),
            (tr("mode_free"), "free")
        ]
        cur_m = self.settings.get("layout_mode", "dock_horizontal")
        for lbl, val in modes:
            self.mode_combo.addItem(lbl, val)
            if val == cur_m:
                self.mode_combo.setCurrentIndex(self.mode_combo.count() - 1)
        self.mode_combo.currentIndexChanged.connect(self.on_mode_changed)

        self.shape_combo = QComboBox()
        cur_shape = self.settings.get("dock_shape", "rounded")
        for key, tr_key in DOCK_SHAPES.items():
            self.shape_combo.addItem(tr(tr_key), key)
            if key == cur_shape:
                self.shape_combo.setCurrentIndex(self.shape_combo.count() - 1)
        self.shape_combo.currentIndexChanged.connect(self.apply_panel_live)

        self.slant_slider = QSlider(Qt.Orientation.Horizontal)
        self.slant_slider.setRange(6, 65)
        self.slant_slider.setValue(self.settings.get("dock_slant", 24))
        self.slant_slider.valueChanged.connect(self.apply_panel_live)

        self.corner_radius_slider = QSlider(Qt.Orientation.Horizontal)
        self.corner_radius_slider.setRange(0, 42)
        self.corner_radius_slider.setValue(self.settings.get("dock_corner_radius", 14))
        self.corner_radius_slider.valueChanged.connect(self.apply_panel_live)

        self.dock_color_btn = QPushButton()
        self.dock_color_btn.clicked.connect(self.pick_dock_bg_color)
        self.update_color_btn_style(self.dock_color_btn, self.settings.get("dock_bg_color", "#12131A"))

        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(0, 255)
        self.opacity_slider.setValue(self.settings.get("dock_bg_opacity", 175))
        self.opacity_slider.valueChanged.connect(self.apply_panel_live)

        self.edge_fade_slider = QSlider(Qt.Orientation.Horizontal)
        self.edge_fade_slider.setRange(0, 100)
        self.edge_fade_slider.setValue(self.settings.get("dock_edge_fade_strength", 85))
        self.edge_fade_slider.valueChanged.connect(self.apply_panel_live)

        self.border_color_btn = QPushButton()
        self.border_color_btn.clicked.connect(self.pick_dock_border_color)
        self.update_color_btn_style(self.border_color_btn, self.settings.get("dock_border_color", "#FFFFFF"))

        self.border_slider = QSlider(Qt.Orientation.Horizontal)
        self.border_slider.setRange(0, 255)
        self.border_slider.setValue(self.settings.get("dock_border_opacity", 65))
        self.border_slider.valueChanged.connect(self.apply_panel_live)

        self.show_bg_cb = QCheckBox(tr("cb_show_dock_bg"))
        self.show_bg_cb.setChecked(self.settings.get("show_dock_bg", True))
        self.show_bg_cb.toggled.connect(self.apply_panel_live)

        self.edge_fade_cb = QCheckBox(tr("cb_edge_fade"))
        self.edge_fade_cb.setChecked(self.settings.get("dock_edge_fade", False))
        self.edge_fade_cb.toggled.connect(self.apply_panel_live)

        self.accent_border_cb = QCheckBox(tr("cb_accent_border"))
        self.accent_border_cb.setChecked(self.settings.get("dock_accent_border", False))
        self.accent_border_cb.toggled.connect(self.apply_panel_live)

        form.addRow(tr("lbl_global_theme"), theme_row)
        form.addRow(tr("lbl_layout_mode"), self.mode_combo)
        form.addRow(tr("lbl_dock_shape"), self.shape_combo)
        form.addRow(tr("lbl_dock_slant"), self.slant_slider)
        form.addRow(tr("lbl_corner_radius"), self.corner_radius_slider)
        form.addRow(tr("lbl_dock_bg_col"), self.dock_color_btn)
        form.addRow(tr("lbl_dock_opacity"), self.opacity_slider)
        form.addRow(tr("lbl_edge_fade"), self.edge_fade_slider)
        form.addRow(tr("lbl_border_col"), self.border_color_btn)
        form.addRow(tr("lbl_border_opacity"), self.border_slider)

        layout.addLayout(form)
        layout.addSpacing(4)
        layout.addWidget(self.show_bg_cb)
        layout.addWidget(self.edge_fade_cb)
        layout.addWidget(self.accent_border_cb)
        layout.addStretch()
        return page

    def _build_folders_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 16, 20, 16)
        form = QFormLayout()
        form.setSpacing(12)

        self.sync_all_cb = QCheckBox(tr("cb_sync_all"))
        self.sync_all_cb.setChecked(self.settings.get("apply_to_all", True))
        self.sync_all_cb.toggled.connect(self.on_folders_changed)

        self.folder_size_spin = QSpinBox()
        self.folder_size_spin.setRange(50, 240)
        self.folder_size_spin.setSingleStep(4)
        self.folder_size_spin.setValue(self.sample_data.get("size", 88))
        self.folder_size_spin.valueChanged.connect(self.on_folders_changed)

        self.folder_font_spin = QSpinBox()
        self.folder_font_spin.setRange(0, 24)
        self.folder_font_spin.setSpecialValueText(tr("font_auto"))
        self.folder_font_spin.setValue(self.sample_data.get("title_font_size", 0))
        self.folder_font_spin.valueChanged.connect(self.on_folders_changed)

        self.theme_combo = QComboBox()
        cur_t = self.sample_data.get("theme", "Тёмное стекло (Win 11)")
        for t_key, (_, _, _, tr_k) in THEMES.items():
            self.theme_combo.addItem(tr(tr_k), t_key)
            if t_key == cur_t:
                self.theme_combo.setCurrentIndex(self.theme_combo.count() - 1)
        self.theme_combo.currentIndexChanged.connect(self.on_theme_combo_changed)

        self.tile_bg_btn = QPushButton(tr("btn_pick_tile_bg"))
        self.tile_bg_btn.clicked.connect(self.pick_tile_bg_color)

        self.tile_acc_btn = QPushButton(tr("btn_pick_tile_acc"))
        self.tile_acc_btn.clicked.connect(self.pick_tile_acc_color)

        self.icon_only_cb = QCheckBox(tr("cb_icon_only"))
        self.icon_only_cb.setChecked(self.sample_data.get("icon_only", False))
        self.icon_only_cb.toggled.connect(self.on_folders_changed)

        self.show_title_cb = QCheckBox(tr("cb_show_title"))
        self.show_title_cb.setChecked(self.sample_data.get("show_title", True))
        self.show_title_cb.toggled.connect(self.on_folders_changed)

        self.show_badge_cb = QCheckBox(tr("cb_show_badge"))
        self.show_badge_cb.setChecked(self.sample_data.get("show_badge", True))
        self.show_badge_cb.toggled.connect(self.on_folders_changed)

        self.fav_folder_cb = QCheckBox(tr("cb_fav_folder"))
        self.fav_folder_cb.setChecked(self.settings.get("show_favorites_folder", False))
        self.fav_folder_cb.toggled.connect(lambda c: self.manager.toggle_favorites_folder(c))

        layout.addWidget(self.sync_all_cb)
        layout.addSpacing(4)
        form.addRow(tr("lbl_folder_size"), self.folder_size_spin)
        form.addRow(tr("lbl_folder_font"), self.folder_font_spin)
        form.addRow(tr("lbl_theme"), self.theme_combo)
        form.addRow(tr("lbl_custom_tile_bg"), self.tile_bg_btn)
        form.addRow(tr("lbl_custom_tile_acc"), self.tile_acc_btn)
        layout.addLayout(form)
        layout.addSpacing(6)
        layout.addWidget(self.icon_only_cb)
        layout.addWidget(self.show_title_cb)
        layout.addWidget(self.show_badge_cb)
        layout.addWidget(self.fav_folder_cb)
        layout.addStretch()
        return page

    def _build_popup_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 16, 20, 16)
        form = QFormLayout()
        form.setSpacing(12)

        self.pop_mode_combo = QComboBox()
        p_modes = [
            (tr("pm_multi"), "multicolumn"),
            (tr("pm_grid"), "grid"),
            (tr("pm_scroll"), "scroll")
        ]
        cur_pm = self.settings.get("popup_display_mode", "multicolumn")
        for lbl, val in p_modes:
            self.pop_mode_combo.addItem(lbl, val)
            if val == cur_pm:
                self.pop_mode_combo.setCurrentIndex(self.pop_mode_combo.count() - 1)
        self.pop_mode_combo.currentIndexChanged.connect(self.apply_popup_live)

        self.pop_w_spin = QSpinBox()
        self.pop_w_spin.setRange(150, 600)
        self.pop_w_spin.setSingleStep(10)
        self.pop_w_spin.setValue(self.settings.get("popup_width", 235))
        self.pop_w_spin.valueChanged.connect(self.apply_popup_live)

        self.pop_ic_spin = QSpinBox()
        self.pop_ic_spin.setRange(16, 64)
        self.pop_ic_spin.setSingleStep(2)
        self.pop_ic_spin.setValue(self.settings.get("popup_icon_size", 24))
        self.pop_ic_spin.valueChanged.connect(self.apply_popup_live)

        self.pop_fn_spin = QSpinBox()
        self.pop_fn_spin.setRange(9, 24)
        self.pop_fn_spin.setValue(self.settings.get("popup_font_size", 13))
        self.pop_fn_spin.valueChanged.connect(self.apply_popup_live)

        self.pop_rows_spin = QSpinBox()
        self.pop_rows_spin.setRange(3, 20)
        self.pop_rows_spin.setValue(self.settings.get("popup_items_per_col", 7))
        self.pop_rows_spin.valueChanged.connect(self.apply_popup_live)

        self.pop_grid_spin = QSpinBox()
        self.pop_grid_spin.setRange(2, 8)
        self.pop_grid_spin.setValue(self.settings.get("popup_grid_cols", 4))
        self.pop_grid_spin.valueChanged.connect(self.apply_popup_live)

        self.pop_maxh_spin = QSpinBox()
        self.pop_maxh_spin.setRange(180, 900)
        self.pop_maxh_spin.setSingleStep(20)
        self.pop_maxh_spin.setValue(self.settings.get("popup_max_height", 360))
        self.pop_maxh_spin.valueChanged.connect(self.apply_popup_live)

        self.popup_color_btn = QPushButton()
        self.popup_color_btn.clicked.connect(self.pick_popup_bg_color)
        self.update_color_btn_style(self.popup_color_btn, self.settings.get("popup_bg_color", "#181922"))

        self.popup_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.popup_opacity_slider.setRange(40, 255)
        self.popup_opacity_slider.setValue(self.settings.get("popup_bg_opacity", 242))
        self.popup_opacity_slider.valueChanged.connect(self.apply_popup_live)

        form.addRow(tr("lbl_pop_mode"), self.pop_mode_combo)
        form.addRow(tr("lbl_pop_w"), self.pop_w_spin)
        form.addRow(tr("lbl_pop_ic"), self.pop_ic_spin)
        form.addRow(tr("lbl_pop_fn"), self.pop_fn_spin)
        form.addRow(tr("lbl_pop_rows"), self.pop_rows_spin)
        form.addRow(tr("lbl_pop_grid"), self.pop_grid_spin)
        form.addRow(tr("lbl_pop_maxh"), self.pop_maxh_spin)
        form.addRow(tr("lbl_pop_col"), self.popup_color_btn)
        form.addRow(tr("lbl_pop_opacity"), self.popup_opacity_slider)

        layout.addLayout(form)
        layout.addStretch()
        return page

    def _build_system_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 14, 20, 14)
        form = QFormLayout()
        form.setSpacing(11)

        self.lang_combo = QComboBox()
        self.lang_combo.addItem("Русский (Russian)", "ru")
        self.lang_combo.addItem("English (Английский)", "en")
        cur_lang = self.settings.get("language", _CURRENT_LANG)
        self.lang_combo.setCurrentIndex(0 if cur_lang == "ru" else 1)
        self.lang_combo.currentIndexChanged.connect(self.on_language_changed)

        self.anim_combo = QComboBox()
        cur_anim = self.settings.get("animation_style", "wave")
        for key, tr_k in ANIMATION_STYLES.items():
            self.anim_combo.addItem(tr(tr_k), key)
            if key == cur_anim:
                self.anim_combo.setCurrentIndex(self.anim_combo.count() - 1)
        self.anim_combo.currentIndexChanged.connect(self.on_system_changed)

        self.hotkey_combo = QComboBox()
        cur_hk = self.settings.get("Summon_hotkey", "alt_space")
        for key, (_, _, tr_k) in HOTKEY_PRESETS.items():
            self.hotkey_combo.addItem(tr(tr_k), key)
            if key == cur_hk:
                self.hotkey_combo.setCurrentIndex(self.hotkey_combo.count() - 1)
        self.hotkey_combo.currentIndexChanged.connect(self.on_hotkey_changed)

        form.addRow(tr("lbl_lang"), self.lang_combo)
        form.addRow(tr("lbl_anim_style"), self.anim_combo)
        form.addRow(tr("lbl_hotkey"), self.hotkey_combo)
        layout.addLayout(form)

        hk_hint = QLabel(tr("hk_hint"))
        hk_hint.setStyleSheet("color: #60CDFF; font-size: 11px; padding: 2px 0 4px 0;")
        layout.addWidget(hk_hint)

        self.hover_open_cb = QCheckBox(tr("cb_hover_open"))
        self.hover_open_cb.setChecked(self.settings.get("open_on_hover", False))
        self.hover_open_cb.toggled.connect(self.on_system_changed)

        self.autohide_cb = QCheckBox(tr("cb_autohide"))
        self.autohide_cb.setChecked(self.settings.get("auto_hide", False))
        self.autohide_cb.toggled.connect(lambda c: self.manager.toggle_auto_hide(c))

        self.run_ind_cb = QCheckBox(tr("cb_run_ind"))
        self.run_ind_cb.setChecked(self.settings.get("show_running_indicator", True))
        self.run_ind_cb.toggled.connect(self.on_system_changed)

        self.top_cb = QCheckBox(tr("cb_always_top"))
        self.top_cb.setChecked(self.settings.get("always_on_top", False))
        self.top_cb.toggled.connect(self.on_top_changed)

        self.autostart_cb = QCheckBox(tr("cb_autostart"))
        self.autostart_cb.setChecked(is_autostart_enabled())
        self.autostart_cb.toggled.connect(self.on_autostart_toggled)

        layout.addWidget(self.hover_open_cb)
        layout.addWidget(self.autohide_cb)
        layout.addWidget(self.run_ind_cb)
        layout.addWidget(self.top_cb)
        layout.addWidget(self.autostart_cb)

        layout.addSpacing(6)
        btn_row1 = QHBoxLayout()
        rescan_btn = QPushButton(tr("btn_rescan"))
        rescan_btn.clicked.connect(self.manager.force_reload_icons)
        btn_row1.addWidget(rescan_btn)

        open_icons_btn = QPushButton(tr("btn_open_icons"))
        open_icons_btn.clicked.connect(lambda: os.startfile(BUNDLED_ICONS_DIR if os.path.exists(BUNDLED_ICONS_DIR) else ICONS_DIR))
        btn_row1.addWidget(open_icons_btn)
        layout.addLayout(btn_row1)

        # Кнопки Экспорта и Импорта настроек
        btn_row2 = QHBoxLayout()
        exp_btn = QPushButton(tr("btn_export_cfg"))
        exp_btn.clicked.connect(self.export_settings_file)
        btn_row2.addWidget(exp_btn)

        imp_btn = QPushButton(tr("btn_import_cfg"))
        imp_btn.clicked.connect(self.import_settings_file)
        btn_row2.addWidget(imp_btn)
        layout.addLayout(btn_row2)

        layout.addStretch()
        return page

    def _build_about_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(10)

        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if self.manager.app_icon:
            icon_lbl.setPixmap(self.manager.app_icon.pixmap(QSize(68, 68)))
        layout.addWidget(icon_lbl)

        title_lbl = QLabel(f"<b style='font-size:18px; color:#FFFFFF;'>{APP_TITLE}</b>")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_lbl)

        ver_lbl = QLabel(f"{tr('version_lbl')} <b>{APP_VERSION}</b>")
        ver_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ver_lbl.setStyleSheet("color: #60CDFF; font-size: 14px;")
        layout.addWidget(ver_lbl)

        desc_lbl = QLabel(tr("about_desc"))
        desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_lbl.setStyleSheet("color: #94A3B8; font-size: 13px;")
        layout.addWidget(desc_lbl)

        layout.addSpacing(6)
        sup_lbl = QLabel(tr("support_header"))
        sup_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sup_lbl.setStyleSheet("color: #E2E8F0; font-size: 13px; font-weight: 600;")
        layout.addWidget(sup_lbl)

        donate_row = QHBoxLayout()
        donate_row.setSpacing(14)

        cloud_btn = QPushButton("CloudTips")
        cloud_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        cloud_btn.setStyleSheet(
            "background-color: #2563EB; color: white; border: 1px solid #60A5FA; "
            "border-radius: 8px; padding: 10px 24px; font-size: 13px; font-weight: bold;"
        )
        cloud_btn.clicked.connect(lambda: webbrowser.open(CLOUDTIPS_URL))
        donate_row.addWidget(cloud_btn)

        dp_btn = QPushButton("DonatePay")
        dp_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        dp_btn.setStyleSheet(
            "background-color: #D97706; color: white; border: 1px solid #FBBF24; "
            "border-radius: 8px; padding: 10px 24px; font-size: 13px; font-weight: bold;"
        )
        dp_btn.clicked.connect(lambda: webbrowser.open(DONATEPAY_URL))
        donate_row.addWidget(dp_btn)

        layout.addLayout(donate_row)

        gh_btn = QPushButton(tr("github_btn"))
        gh_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        gh_btn.setStyleSheet(
            "background-color: #24292F; color: white; border: 1px solid #57606A; "
            "border-radius: 8px; padding: 9px 24px; font-size: 13px; font-weight: bold;"
        )
        gh_btn.clicked.connect(lambda: webbrowser.open(GITHUB_URL))
        layout.addWidget(gh_btn)

        layout.addStretch()
        return page

    # --- Управление глобальными темами и экспортом ---
    def on_global_theme_selected(self):
        t_key = self.global_theme_combo.currentData()
        if not t_key or t_key == "__custom__":
            self.settings["global_theme"] = "__custom__"
            return

        theme_dict = BUILTIN_GLOBAL_THEMES.get(t_key) or self.settings.get("custom_global_themes", {}).get(t_key)
        if not theme_dict:
            return

        self.settings["global_theme"] = t_key
        self.settings["dock_bg_color"] = theme_dict["dock_bg_color"]
        self.settings["dock_border_color"] = theme_dict["dock_border_color"]
        self.settings["popup_bg_color"] = theme_dict["popup_bg_color"]

        for f in self.manager.folders_data:
            if f.get("is_favorites"):
                continue
            if theme_dict.get("folder_theme") and theme_dict["folder_theme"] in THEMES:
                f["theme"] = theme_dict["folder_theme"]
                f["custom_bg_color"] = ""
                f["custom_accent_color"] = ""
            else:
                f["theme"] = "Свой цвет"
                f["custom_bg_color"] = theme_dict.get("folder_bg_color", "#2B2D38")
                f["custom_accent_color"] = theme_dict.get("folder_accent_color", "#60CDFF")

        self.update_color_btn_style(self.dock_color_btn, self.settings["dock_bg_color"])
        self.update_color_btn_style(self.border_color_btn, self.settings["dock_border_color"])
        self.update_color_btn_style(self.popup_color_btn, self.settings["popup_bg_color"])
        self.manager.refresh_appearance()
        self.manager.save_config()

    def save_custom_global_theme(self):
        name, ok = QInputDialog.getText(self, tr("dlg_save_theme_t"), tr("dlg_save_theme_l"))
        if ok and name.strip():
            name = name.strip()
            c1, _, acc = get_tile_colors(self.sample_data)
            custom_map = self.settings.setdefault("custom_global_themes", {})
            custom_map[name] = {
                "dock_bg_color": self.settings.get("dock_bg_color", "#12131A"),
                "dock_border_color": self.settings.get("dock_border_color", "#FFFFFF"),
                "popup_bg_color": self.settings.get("popup_bg_color", "#181922"),
                "folder_bg_color": self.sample_data.get("custom_bg_color") or c1,
                "folder_accent_color": self.sample_data.get("custom_accent_color") or acc,
                "folder_theme": ""
            }
            self.settings["global_theme"] = name
            self._populate_global_theme_combo()
            self.manager.save_config()

    def export_settings_file(self):
        file_p, _ = QFileDialog.getSaveFileName(
            self, tr("dlg_export_t"), os.path.expanduser("~\\Desktop\\DesktopFolders_Backup.json"), tr("json_filter")
        )
        if file_p:
            self.manager.save_config()
            try:
                shutil.copy2(CONFIG_FILE, file_p)
                QMessageBox.information(self, APP_TITLE, tr("msg_export_ok"))
            except Exception as e:
                QMessageBox.warning(self, APP_TITLE, str(e))

    def import_settings_file(self):
        file_p, _ = QFileDialog.getOpenFileName(
            self, tr("dlg_import_t"), os.path.expanduser("~\\Desktop"), tr("json_filter")
        )
        if file_p and os.path.exists(file_p):
            try:
                with open(file_p, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                if isinstance(raw, dict) and "folders" in raw:
                    self.manager.settings.update(raw.get("settings", {}))
                    self.manager.folders_data = raw.get("folders", [])
                    self.manager.save_config()
                    self.manager.rebuild_ui()
                    self.close()
                    QMessageBox.information(None, APP_TITLE, tr("msg_import_ok"))
            except Exception as e:
                QMessageBox.warning(self, APP_TITLE, str(e))

    def on_language_changed(self):
        new_lang = self.lang_combo.currentData()
        self.manager.set_language(new_lang)
        self.close()
        QTimer.singleShot(20, lambda: self.manager.open_settings_dialog(self.target_tile, initial_tab=3))

    def on_hotkey_changed(self):
        self.settings["Summon_hotkey"] = self.hotkey_combo.currentData()
        self.manager.register_global_hotkey()
        self.manager.save_config()

    def on_autostart_toggled(self, checked):
        set_autostart(checked)
        self.manager.update_tray_menu()

    def update_color_btn_style(self, btn: QPushButton, hex_color: str):
        c = QColor(hex_color)
        text_col = "#000000" if is_color_light(c.name()) else "#FFFFFF"
        btn.setText(f"{tr('palette_btn')} ({c.name().upper()})")
        btn.setStyleSheet(
            f"background-color: {c.name()}; color: {text_col}; border: 1px solid rgba(255,255,255,60); "
            f"border-radius: 6px; padding: 5px 12px; font-weight: 600;"
        )

    def on_mode_changed(self):
        new_m = self.mode_combo.currentData()
        self.manager.set_layout_mode(new_m)

    def apply_panel_live(self):
        old_shape = self.settings.get("dock_shape")
        old_slant = self.settings.get("dock_slant")

        self.settings["dock_shape"] = self.shape_combo.currentData()
        self.settings["dock_slant"] = self.slant_slider.value()
        self.settings["dock_corner_radius"] = self.corner_radius_slider.value()
        self.settings["dock_bg_opacity"] = self.opacity_slider.value()
        self.settings["dock_edge_fade"] = self.edge_fade_cb.isChecked()
        self.settings["dock_edge_fade_strength"] = self.edge_fade_slider.value()
        self.settings["dock_border_opacity"] = self.border_slider.value()
        self.settings["dock_accent_border"] = self.accent_border_cb.isChecked()
        self.settings["show_dock_bg"] = self.show_bg_cb.isChecked()

        if self.manager.dock_window:
            if old_shape != self.settings["dock_shape"] or old_slant != self.settings["dock_slant"]:
                self.manager.dock_window.update_margins_and_repaint()
            else:
                self.manager.dock_window.update()
        self.save_timer.start(250)

    def on_folders_changed(self):
        self.settings["apply_to_all"] = self.sync_all_cb.isChecked()
        targets = self.manager.folders_data if self.settings["apply_to_all"] else [self.sample_data]
        for f in targets:
            f["size"] = self.folder_size_spin.value()
            f["title_font_size"] = self.folder_font_spin.value()
            f["icon_only"] = self.icon_only_cb.isChecked()
            f["show_title"] = self.show_title_cb.isChecked()
            f["show_badge"] = self.show_badge_cb.isChecked()
        self.manager.refresh_appearance()
        self.save_timer.start(250)

    def on_theme_combo_changed(self):
        t_name = self.theme_combo.currentData()
        targets = self.manager.folders_data if self.settings.get("apply_to_all", True) else [self.sample_data]
        for f in targets:
            if f.get("is_favorites") and len(targets) > 1 and t_name != "Золотое Избранное":
                continue
            f["theme"] = t_name
            f["custom_bg_color"] = ""
            f["custom_accent_color"] = ""
        self.manager.refresh_appearance()
        self.save_timer.start(250)

    def pick_tile_bg_color(self):
        c1, _, _ = get_tile_colors(self.sample_data)
        col = QColorDialog.getColor(QColor(c1), self)
        if col.isValid():
            self.settings["global_theme"] = "__custom__"
            self._populate_global_theme_combo()
            targets = self.manager.folders_data if self.settings.get("apply_to_all", True) else [self.sample_data]
            for f in targets:
                f["custom_bg_color"] = col.name()
                f["theme"] = "Свой цвет"
            self.manager.refresh_appearance()
            self.manager.save_config()

    def pick_tile_acc_color(self):
        _, _, acc = get_tile_colors(self.sample_data)
        col = QColorDialog.getColor(QColor(acc), self)
        if col.isValid():
            self.settings["global_theme"] = "__custom__"
            self._populate_global_theme_combo()
            targets = self.manager.folders_data if self.settings.get("apply_to_all", True) else [self.sample_data]
            for f in targets:
                f["custom_accent_color"] = col.name()
            self.manager.refresh_appearance()
            self.manager.save_config()

    def apply_popup_live(self):
        self.settings["popup_display_mode"] = self.pop_mode_combo.currentData()
        self.settings["popup_width"] = self.pop_w_spin.value()
        self.settings["popup_icon_size"] = self.pop_ic_spin.value()
        self.settings["popup_font_size"] = self.pop_fn_spin.value()
        self.settings["popup_items_per_col"] = self.pop_rows_spin.value()
        self.settings["popup_grid_cols"] = self.pop_grid_spin.value()
        self.settings["popup_max_height"] = self.pop_maxh_spin.value()
        self.settings["popup_bg_opacity"] = self.popup_opacity_slider.value()
        self.settings["popup_padding"] = max(4, self.pop_ic_spin.value() // 3)
        self.save_timer.start(250)

    def on_system_changed(self):
        self.settings["animation_style"] = self.anim_combo.currentData()
        self.settings["hover_animation"] = (self.settings["animation_style"] != "none")
        self.settings["open_on_hover"] = self.hover_open_cb.isChecked()
        self.settings["show_running_indicator"] = self.run_ind_cb.isChecked()
        if self.manager.dock_window and not self.settings["hover_animation"]:
            self.manager.dock_window.reset_wave_targets()
        self.manager.trigger_async_process_scan()
        self.manager.refresh_appearance()
        self.save_timer.start(250)

    def on_top_changed(self, checked):
        self.settings["always_on_top"] = checked
        self.manager.save_config()
        self.manager.rebuild_ui()

    def pick_dock_bg_color(self):
        cur = QColor(self.settings.get("dock_bg_color", "#12131A"))
        col = QColorDialog.getColor(cur, self)
        if col.isValid():
            self.settings["dock_bg_color"] = col.name()
            self.settings["global_theme"] = "__custom__"
            self._populate_global_theme_combo()
            self.update_color_btn_style(self.dock_color_btn, col.name())
            self.apply_panel_live()

    def pick_dock_border_color(self):
        cur = QColor(self.settings.get("dock_border_color", "#FFFFFF"))
        col = QColorDialog.getColor(cur, self)
        if col.isValid():
            self.settings["dock_border_color"] = col.name()
            self.settings["dock_accent_border"] = False
            self.accent_border_cb.setChecked(False)
            self.settings["global_theme"] = "__custom__"
            self._populate_global_theme_combo()
            self.update_color_btn_style(self.border_color_btn, col.name())
            self.apply_panel_live()

    def pick_popup_bg_color(self):
        cur = QColor(self.settings.get("popup_bg_color", "#181922"))
        col = QColorDialog.getColor(cur, self)
        if col.isValid():
            self.settings["popup_bg_color"] = col.name()
            self.settings["global_theme"] = "__custom__"
            self._populate_global_theme_combo()
            self.update_color_btn_style(self.popup_color_btn, col.name())
            self.apply_popup_live()


class IconPickerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(None)
        self.selected_icon = None
        self.setWindowTitle(tr("gallery_title"))
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowCloseButtonHint)
        self.setFixedSize(520, 420)
        self.setStyleSheet("""
            QDialog { background-color: #1A1B23; color: #FFFFFF; font-family: 'Segoe UI'; }
            QLabel { color: #D0D4DC; font-size: 13px; }
            QPushButton.IconCard {
                background-color: rgba(255, 255, 255, 10);
                border: 1px solid rgba(255, 255, 255, 22);
                border-radius: 12px; padding: 8px; color: #E2E8F0; font-size: 11px;
            }
            QPushButton.IconCard:hover {
                background-color: rgba(96, 205, 255, 45);
                border: 1.5px solid #60CDFF;
            }
            QPushButton#BrowseBtn {
                background-color: #2B579A; color: white; border: none;
                border-radius: 7px; padding: 8px 14px; font-weight: 600;
            }
            QPushButton#BrowseBtn:hover { background-color: #3B69B0; }
            QScrollArea {
                border: 1px solid rgba(255, 255, 255, 18);
                border-radius: 10px; background-color: rgba(0, 0, 0, 45);
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        top_bar = QHBoxLayout()
        info_lbl = QLabel(f"{tr('gallery_pack_dir')} <b>{BUNDLED_ICONS_DIR}</b>")
        info_lbl.setWordWrap(True)
        top_bar.addWidget(info_lbl, 1)

        open_dir_btn = QPushButton(tr("btn_open_folder"))
        open_dir_btn.setObjectName("BrowseBtn")
        open_dir_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        open_dir_btn.clicked.connect(lambda: os.startfile(BUNDLED_ICONS_DIR if os.path.exists(BUNDLED_ICONS_DIR) else ICONS_DIR))
        top_bar.addWidget(open_dir_btn)
        layout.addLayout(top_bar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        grid_container = QWidget()
        grid_container.setStyleSheet("background: transparent;")
        grid = QGridLayout(grid_container)
        grid.setContentsMargins(12, 12, 12, 12)
        grid.setSpacing(12)

        valid_exts = (".png", ".ico", ".webp", ".jpg", ".jpeg", ".bmp", ".svg")
        found_files = {}
        for d in (BUNDLED_ICONS_DIR, USER_ICONS_DIR):
            if os.path.isdir(d):
                for f in os.listdir(d):
                    if f.lower().endswith(valid_exts) and f not in found_files:
                        found_files[f] = os.path.join(d, f)

        if not found_files:
            empty_lbl = QLabel(tr("gallery_empty"))
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_lbl.setStyleSheet("color: #8892B0; font-size: 13px; padding: 40px;")
            grid.addWidget(empty_lbl, 0, 0)
        else:
            cols = 4
            for idx, (fname, full_p) in enumerate(sorted(found_files.items())):
                btn = QPushButton()
                btn.setProperty("class", "IconCard")
                btn.setFixedSize(105, 105)
                btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

                btn_layout = QVBoxLayout(btn)
                btn_layout.setContentsMargins(6, 6, 6, 4)
                btn_layout.setSpacing(4)

                img_lbl = QLabel()
                img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                img_lbl.setStyleSheet("background: transparent; border: none;")
                master_pix = get_master_folder_pixmap(full_p)
                img_lbl.setPixmap(master_pix.scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

                name_short = os.path.splitext(fname)[0]
                if len(name_short) > 12:
                    name_short = name_short[:11] + "…"
                txt_lbl = QLabel(name_short)
                txt_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                txt_lbl.setStyleSheet("background: transparent; border: none; font-size: 11px; color: #CBD5E0;")

                btn_layout.addWidget(img_lbl, 1)
                btn_layout.addWidget(txt_lbl)

                rel_path = os.path.join("icons", fname)
                btn.clicked.connect(lambda checked, p=rel_path: self.choose_icon(p))
                grid.addWidget(btn, idx // cols, idx % cols)

        scroll.setWidget(grid_container)
        layout.addWidget(scroll, 1)

        bottom_bar = QHBoxLayout()
        browse_other_btn = QPushButton(tr("btn_browse_other"))
        browse_other_btn.setObjectName("BrowseBtn")
        browse_other_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        browse_other_btn.clicked.connect(self.browse_custom_file)
        bottom_bar.addWidget(browse_other_btn)
        bottom_bar.addStretch()
        layout.addLayout(bottom_bar)

    def choose_icon(self, path):
        self.selected_icon = path
        self.accept()

    def browse_custom_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, tr("dlg_pick_icon"), "", tr("img_filter")
        )
        if file_path:
            try:
                dest = os.path.join(ICONS_DIR, os.path.basename(file_path))
                if os.path.abspath(file_path) != os.path.abspath(dest):
                    shutil.copy2(file_path, dest)
                self.selected_icon = os.path.join("icons", os.path.basename(file_path))
            except Exception:
                self.selected_icon = file_path
            self.accept()
            
            
class DraggableAppButton(QPushButton):
    def __init__(self, popup, app_data, index, is_running=False, is_grid_mode=False,
                 item_w=220, icon_sz=24, font_sz=13, pad_v=7, accent_color="#60CDFF", is_light_bg=False):
        super().__init__()
        self.popup = popup
        self.app_data = app_data
        self.index = index
        self.is_running = is_running
        self.is_grid_mode = is_grid_mode
        self.icon_sz = icon_sz
        self.font_sz = font_sz
        self.accent_color = accent_color
        self.is_light_bg = is_light_bg
        self.is_separator = app_data.get("is_separator", False)
        self.is_text_truncated = False

        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.drag_start_global = None
        self.is_dragging_item = False

        # Таймер долгого удержания курсора для показа полного названия, если оно не поместилось
        self.full_name_timer = QTimer(self)
        self.full_name_timer.setSingleShot(True)
        self.full_name_timer.timeout.connect(self.show_full_name_tooltip)

        clean_name = (
            app_data.get("name", "")
            .replace(" — ярлык", "")
            .replace(" - Ярлык", "")
            .replace(" - Shortcut", "")
            .replace(".lnk", "")
        )
        self.clean_name = clean_name

        if self.is_separator:
            self.app_icon = QIcon()
            if is_grid_mode:
                tile_sz = max(82, icon_sz * 2 + 36)
                self.setFixedSize(tile_sz, 26)
            else:
                self.setFixedSize(item_w, 24)
            return

        self.app_icon = get_accurate_file_icon(app_data)

        if is_grid_mode:
            tile_sz = max(82, icon_sz * 2 + 36)
            self.setFixedSize(tile_sz, tile_sz)
            self._grid_pixmap = self.app_icon.pixmap(QSize(self.icon_sz + 10, self.icon_sz + 10))
        else:
            self.setIcon(self.app_icon)
            self.setIconSize(QSize(icon_sz, icon_sz))
            self.setFixedWidth(item_w)
            self.setProperty("class", "AppItem")

            # Проверяем, помещается ли название целиком в ширину кнопки списка
            fm = self.fontMetrics()
            avail_text_w = item_w - icon_sz - 42
            if fm.horizontalAdvance(clean_name) > avail_text_w:
                self.is_text_truncated = True
                elided = fm.elidedText(clean_name, Qt.TextElideMode.ElideRight, avail_text_w)
                self.setText(f"  {elided}")
            else:
                self.setText(f"  {clean_name}")

    def enterEvent(self, event):
        if not self.is_separator and (self.is_text_truncated or self.is_grid_mode):
            self.full_name_timer.start(480)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.full_name_timer.stop()
        QToolTip.hideText()
        super().leaveEvent(event)

    def show_full_name_tooltip(self):
        if self.underMouse() and self.clean_name:
            QToolTip.showText(QCursor.pos(), self.clean_name, self)

    def paintEvent(self, event):
        # 1. Отрисовка горизонтального разделителя (с текстом или просто линии)
        if self.is_separator:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            r = QRectF(self.rect())
            mid_y = r.center().y()

            line_col = QColor(self.accent_color) if (self.underMouse() or self.is_dragging_item) else (
                QColor(0, 0, 0, 55) if self.is_light_bg else QColor(255, 255, 255, 45)
            )
            text_col = QColor("#1E293B") if self.is_light_bg else QColor(255, 255, 255, 165)

            if self.clean_name.strip():
                painter.setFont(QFont("Segoe UI", max(8, self.font_sz - 3), QFont.Weight.DemiBold))
                fm = painter.fontMetrics()
                tw = fm.horizontalAdvance(self.clean_name) + 12
                cx = r.center().x()

                painter.setPen(QPen(line_col, 1.3))
                if cx - tw / 2 > r.left() + 6:
                    painter.drawLine(QPointF(r.left() + 6, mid_y), QPointF(cx - tw / 2, mid_y))
                if cx + tw / 2 < r.right() - 6:
                    painter.drawLine(QPointF(cx + tw / 2, mid_y), QPointF(r.right() - 6, mid_y))

                painter.setPen(text_col)
                painter.drawText(r, Qt.AlignmentFlag.AlignCenter, self.clean_name)
            else:
                painter.setPen(QPen(line_col, 1.5))
                painter.drawLine(QPointF(r.left() + 8, mid_y), QPointF(r.right() - 8, mid_y))
            return

        # 2. Отрисовка обычной кнопки в режиме списка
        if not self.is_grid_mode:
            super().paintEvent(event)
            if self.is_dragging_item:
                painter = QPainter(self)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.setPen(QPen(QColor("#F6AD55"), 2.0, Qt.PenStyle.DashLine))
                painter.setBrush(QColor(246, 173, 85, 30))
                painter.drawRoundedRect(QRectF(self.rect()).adjusted(1, 1, -1, -1), 8, 8)
            if self.is_running:
                painter = QPainter(self)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                dot_x = self.width() - 16
                dot_y = (self.height() - 8) // 2
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(72, 187, 120, 90))
                painter.drawEllipse(dot_x - 2, dot_y - 2, 12, 12)
                painter.setBrush(QColor("#48BB78"))
                painter.drawEllipse(dot_x, dot_y, 8, 8)
            return

        # 3. Отрисовка плитки в режиме Grid
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        rect = QRectF(self.rect()).adjusted(2, 2, -2, -2)
        hovered = self.underMouse()

        if self.is_light_bg:
            bg = QColor(246, 173, 85, 55) if self.is_dragging_item else QColor(0, 0, 0, 18 if hovered else 7)
            border = QColor("#F6AD55") if self.is_dragging_item else (QColor(self.accent_color) if hovered else QColor(0, 0, 0, 25))
            txt_col = QColor("#1E293B")
        else:
            bg = QColor(246, 173, 85, 45) if self.is_dragging_item else QColor(255, 255, 255, 26 if hovered else 9)
            border = QColor("#F6AD55") if self.is_dragging_item else (QColor(self.accent_color) if hovered else QColor(255, 255, 255, 16))
            txt_col = QColor("#F2F4F8")

        painter.setBrush(bg)
        painter.setPen(QPen(border, 1.8 if self.is_dragging_item else (1.2 if hovered else 1.0)))
        painter.drawRoundedRect(rect, 10, 10)

        if not self._grid_pixmap.isNull():
            ix = int(rect.center().x() - self._grid_pixmap.width() / 2)
            iy = int(rect.top() + 10)
            painter.drawPixmap(ix, iy, self._grid_pixmap)

        if self.is_running:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#48BB78"))
            painter.drawEllipse(int(rect.right() - 13), int(rect.top() + 6), 7, 7)

        text_rect = QRectF(rect.left() + 4, rect.bottom() - 26, rect.width() - 8, 22)
        painter.setFont(QFont("Segoe UI", max(8, self.font_sz - 2)))
        painter.setPen(txt_col)
        fm = painter.fontMetrics()
        if fm.horizontalAdvance(self.clean_name) > int(text_rect.width()):
            self.is_text_truncated = True
        elided = fm.elidedText(self.clean_name, Qt.TextElideMode.ElideRight, int(text_rect.width()))
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, elided)

    def mousePressEvent(self, event):
        self.full_name_timer.stop()
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_global = event.globalPosition().toPoint()
            self.is_dragging_item = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (event.buttons() & Qt.MouseButton.LeftButton) and self.drag_start_global:
            cur_global = event.globalPosition().toPoint()
            if (cur_global - self.drag_start_global).manhattanLength() > 7:
                self.is_dragging_item = True
                self.setDown(False)
                self.update()
                target_btn = self.popup.find_button_at_global(cur_global)
                if target_btn and target_btn is not self:
                    self.popup.swap_items_live(self, target_btn)
                    self.drag_start_global = cur_global
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.is_dragging_item:
                self.is_dragging_item = False
                self.drag_start_global = None
                self.setDown(False)
                self.update()
                self.popup.tile.manager.save_config()
                self.popup.refresh_after_drag()
                event.accept()
                return
            self.drag_start_global = None
        super().mouseReleaseEvent(event)


class DropdownPopup(QWidget):
    def __init__(self, tile_widget, open_direction="down", running_procs=None):
        super().__init__()
        self.tile = tile_widget
        self.settings = tile_widget.manager.settings
        self.apps_list = tile_widget.data.get("apps", [])
        self.open_direction = open_direction
        self.running_procs = running_procs if running_procs is not None else set()
        self.app_buttons = []
        self._hovered_sibling = None
        self._sibling_dwell_ticks = 0
        self._outside_ticks = 0

        is_fav = tile_widget.data.get("is_favorites", False)
        _, _, self.accent_color = get_tile_colors(tile_widget.data)

        pop_w = self.settings.get("popup_width", 235)
        icon_sz = self.settings.get("popup_icon_size", 24)
        font_sz = self.settings.get("popup_font_size", 13)
        pad_v = self.settings.get("popup_padding", 7)
        max_h_limit = self.settings.get("popup_max_height", 360)
        popup_style = self.settings.get("popup_display_mode", "multicolumn")
        items_per_col = max(3, self.settings.get("popup_items_per_col", 7))
        grid_cols = max(2, self.settings.get("popup_grid_cols", 4))

        self.setWindowFlags(
            Qt.WindowType.Tool |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowDoesNotAcceptFocus |
            Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(12, 10, 12, 12)

        container = QFrame(self)
        container.setObjectName("MainCard")

        border_accent = (
            f"border-left: 3px solid {self.accent_color};"
            if open_direction == "side"
            else f"border-top: 2px solid {self.accent_color};"
        )

        pop_bg_hex = self.settings.get("popup_bg_color", "#181922")
        self.is_light_popup = is_color_light(pop_bg_hex)
        pop_bg_col = QColor(pop_bg_hex)
        pop_bg_alpha = self.settings.get("popup_bg_opacity", 242)
        rgba_str = f"rgba({pop_bg_col.red()}, {pop_bg_col.green()}, {pop_bg_col.blue()}, {pop_bg_alpha})"

        hdr_col = "rgba(15, 23, 42, 195)" if self.is_light_popup else "rgba(255, 255, 255, 175)"
        item_txt_col = "#1E293B" if self.is_light_popup else "#F2F4F8"
        item_bg_col = "rgba(0, 0, 0, 10)" if self.is_light_popup else "rgba(255, 255, 255, 8)"
        item_hover_bg = "rgba(0, 0, 0, 22)" if self.is_light_popup else "rgba(255, 255, 255, 26)"
        btn_small_bg = "rgba(0, 0, 0, 14)" if self.is_light_popup else "rgba(255, 255, 255, 14)"

        container.setStyleSheet(f"""
            QFrame#MainCard {{
                background-color: {rgba_str};
                border: 1px solid rgba(255, 255, 255, 35);
                {border_accent}
                border-radius: 12px;
            }}
            QFrame.SubColCard {{
                background-color: rgba(255, 255, 255, 4);
                border: 1px solid rgba(255, 255, 255, 12);
                border-radius: 9px;
            }}
            QLabel#HeaderTitle {{
                color: {hdr_col};
                font-family: 'Segoe UI';
                font-size: {max(10, font_sz - 2)}px;
                font-weight: 600;
            }}
            QPushButton#AddSmallBtn {{
                background-color: {btn_small_bg};
                color: {item_txt_col}; border: 1px solid rgba(128, 128, 128, 40);
                border-radius: 6px; padding: 2px 7px;
                font-family: 'Segoe UI'; font-size: {max(10, font_sz - 2)}px;
            }}
            QPushButton#AddSmallBtn:hover {{
                background-color: {self.accent_color}; color: #111111; font-weight: bold;
            }}
            QPushButton.AppItem {{
                background-color: {item_bg_col};
                color: {item_txt_col}; border: 1px solid rgba(128, 128, 128, 22);
                border-radius: 8px;
                padding: {pad_v}px 22px {pad_v}px 10px;
                text-align: left;
                font-family: 'Segoe UI';
                font-size: {font_sz}px;
            }}
            QPushButton.AppItem:hover {{
                background-color: {item_hover_bg};
                border: 1px solid {self.accent_color};
            }}
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{ background: transparent; width: 6px; }}
            QScrollBar::handle:vertical {{ background: rgba(128, 128, 128, 80); border-radius: 3px; }}
            QToolTip {{
                background-color: #1E202B; color: #FFFFFF;
                border: 1px solid {self.accent_color}; border-radius: 5px;
                padding: 4px 8px; font-family: 'Segoe UI'; font-size: 12px;
            }}
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 165))
        shadow.setOffset(0, 4)
        container.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(container)
        card_layout.setContentsMargins(10, 8, 10, 10)
        card_layout.setSpacing(6)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(4, 0, 2, 2)
        header_layout.setSpacing(4)
        title_lbl = QLabel(tile_widget.data.get('title', tr('def_shortcut')).upper())
        title_lbl.setObjectName("HeaderTitle")
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()

        if len(self.apps_list) > 1:
            sort_btn = QPushButton("A-Z" if _CURRENT_LANG == "en" else "А-Я")
            sort_btn.setObjectName("AddSmallBtn")
            sort_btn.setToolTip(tr("btn_sort_tip"))
            sort_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            sort_btn.clicked.connect(self.sort_apps_by_name)
            header_layout.addWidget(sort_btn)

        view_toggle_btn = QPushButton(tr("btn_grid") if popup_style != "grid" else tr("btn_list"))
        view_toggle_btn.setObjectName("AddSmallBtn")
        view_toggle_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        view_toggle_btn.clicked.connect(self.toggle_grid_mode)
        header_layout.addWidget(view_toggle_btn)

        add_sep_btn = QPushButton("—")
        add_sep_btn.setObjectName("AddSmallBtn")
        add_sep_btn.setToolTip(tr("btn_add_sep_tip"))
        add_sep_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        add_sep_btn.clicked.connect(lambda: self.add_separator_at())
        header_layout.addWidget(add_sep_btn)

        add_web_btn = QPushButton(tr("btn_add_web"))
        add_web_btn.setObjectName("AddSmallBtn")
        add_web_btn.setToolTip(tr("btn_add_web_tip"))
        add_web_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        add_web_btn.clicked.connect(self.add_web_link_from_popup)
        header_layout.addWidget(add_web_btn)

        add_dir_btn = QPushButton(tr("btn_add_dir"))
        add_dir_btn.setObjectName("AddSmallBtn")
        add_dir_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        add_dir_btn.clicked.connect(self.add_folder_link_from_popup)
        header_layout.addWidget(add_dir_btn)

        if not is_fav:
            add_btn = QPushButton(tr("btn_add_file"))
            add_btn.setObjectName("AddSmallBtn")
            add_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            add_btn.clicked.connect(self.add_app_from_popup)
            header_layout.addWidget(add_btn)

        card_layout.addLayout(header_layout)

        item_width = pop_w - 12

        if not self.apps_list:
            hint_txt = tr("empty_fav_hint") if is_fav else tr("empty_reg_hint")
            empty_label = QLabel(hint_txt)
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet(f"color: rgba(128,128,128,160); font-size: {max(11, font_sz-1)}px; padding: 16px 8px;")
            empty_label.setFixedWidth(pop_w)
            card_layout.addWidget(empty_label)

        elif popup_style == "grid":
            grid_frame = QFrame()
            grid_frame.setProperty("class", "SubColCard")
            grid_layout = QGridLayout(grid_frame)
            grid_layout.setContentsMargins(8, 8, 8, 8)
            grid_layout.setSpacing(8)

            for idx, app_data in enumerate(self.apps_list):
                btn = self.create_app_button(app_data, idx, item_width, icon_sz, font_sz, pad_v, is_grid=True)
                grid_layout.addWidget(btn, idx // grid_cols, idx % grid_cols)

            card_layout.addWidget(grid_frame)

        elif popup_style == "multicolumn" and len(self.apps_list) > items_per_col:
            columns_layout = QHBoxLayout()
            columns_layout.setContentsMargins(0, 2, 0, 0)
            columns_layout.setSpacing(8)

            for col_start in range(0, len(self.apps_list), items_per_col):
                chunk = self.apps_list[col_start:col_start + items_per_col]
                col_frame = QFrame()
                col_frame.setProperty("class", "SubColCard")
                col_vbox = QVBoxLayout(col_frame)
                col_vbox.setContentsMargins(6, 6, 6, 6)
                col_vbox.setSpacing(5)

                for local_idx, app_data in enumerate(chunk):
                    real_idx = col_start + local_idx
                    btn = self.create_app_button(app_data, real_idx, item_width, icon_sz, font_sz, pad_v, is_grid=False)
                    col_vbox.addWidget(btn)

                col_vbox.addStretch()
                columns_layout.addWidget(col_frame)

            card_layout.addLayout(columns_layout)

        else:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll_content = QWidget()
            scroll_content.setStyleSheet("background: transparent;")
            list_layout = QVBoxLayout(scroll_content)
            list_layout.setContentsMargins(0, 2, 0, 0)
            list_layout.setSpacing(5)

            for idx, app_data in enumerate(self.apps_list):
                btn = self.create_app_button(app_data, idx, item_width, icon_sz, font_sz, pad_v, is_grid=False)
                list_layout.addWidget(btn)

            scroll.setWidget(scroll_content)
            row_h = icon_sz + pad_v * 2 + 10
            calc_h = len(self.apps_list) * row_h + 8
            max_h = calc_h if popup_style == "multicolumn" else min(max_h_limit, max(75, calc_h))
            scroll.setFixedHeight(max_h)
            scroll.setFixedWidth(pop_w)
            card_layout.addWidget(scroll)

        outer_layout.addWidget(container)

        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(80)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.hover_watch_timer = QTimer(self)
        self.hover_watch_timer.timeout.connect(self.watch_cursor_and_outside_clicks)
        self.hover_watch_timer.start(40)

    def add_separator_at(self, insert_idx=None):
        """Добавляет горизонтальный разделитель в выпадающий список"""
        self.hover_watch_timer.stop()
        label_txt, ok = QInputDialog.getText(None, tr("dlg_sep_t"), tr("dlg_sep_l"))
        if ok:
            sep_item = {"name": label_txt.strip(), "path": "", "is_separator": True, "exe_name": ""}
            if insert_idx is not None and 0 <= insert_idx <= len(self.apps_list):
                self.apps_list.insert(insert_idx, sep_item)
            else:
                self.apps_list.append(sep_item)
            self.tile.update()
            self.tile.manager.save_config()
            self.close()
            self.tile.last_popup_close_time = 0.0
            self.tile.open_dropdown()
        else:
            self.hover_watch_timer.start(40)

    def move_item_to_another_folder(self, item_index: int, target_folder_data: dict):
        """Переносит ярлык из текущей папки в выбранную другую папку"""
        if 0 <= item_index < len(self.apps_list):
            item = self.apps_list.pop(item_index)
            target_folder_data.setdefault("apps", []).append(item)
            self.tile.manager.refresh_appearance()
            self.tile.manager.save_config()
            self.close()
            self.tile.last_popup_close_time = 0.0
            if self.apps_list:
                self.tile.open_dropdown()

    def find_button_at_global(self, global_pt: QPoint):
        for btn in self.app_buttons:
            tl = btn.mapToGlobal(QPoint(0, 0))
            r = QRectF(tl.x(), tl.y(), btn.width(), btn.height())
            if r.contains(QPointF(global_pt)):
                return btn
        return None

    def swap_items_live(self, btn1: DraggableAppButton, btn2: DraggableAppButton):
        idx1, idx2 = btn1.index, btn2.index
        if idx1 == idx2:
            return
        self.apps_list[idx1], self.apps_list[idx2] = self.apps_list[idx2], self.apps_list[idx1]
        btn1.index, btn2.index = idx2, idx1
        self.app_buttons[idx1], self.app_buttons[idx2] = self.app_buttons[idx2], self.app_buttons[idx1]

        parent1 = btn1.parentWidget()
        parent2 = btn2.parentWidget()
        if parent1 and parent1 is parent2:
            lay = parent1.layout()
            if isinstance(lay, QVBoxLayout):
                for b in self.app_buttons:
                    if b.parentWidget() is parent1:
                        lay.removeWidget(b)
                for b in self.app_buttons:
                    if b.parentWidget() is parent1:
                        lay.insertWidget(lay.count() - 1 if lay.count() > 0 and lay.itemAt(lay.count()-1).spacerItem() else lay.count(), b)
            elif isinstance(lay, QGridLayout):
                grid_cols = max(2, self.settings.get("popup_grid_cols", 4))
                for b in self.app_buttons:
                    lay.removeWidget(b)
                for i, b in enumerate(self.app_buttons):
                    lay.addWidget(b, i // grid_cols, i % grid_cols)
        self.update()

    def refresh_after_drag(self):
        self.close()
        self.tile.last_popup_close_time = 0.0
        self.tile.open_dropdown()

    def sort_apps_by_name(self):
        if len(self.apps_list) <= 1:
            return
        current_names = [a.get("name", "").lower().strip() for a in self.apps_list]
        sorted_asc = sorted(current_names)
        reverse_flag = (current_names == sorted_asc)
        self.apps_list.sort(key=lambda a: a.get("name", "").lower().strip(), reverse=reverse_flag)
        self.tile.manager.save_config()
        self.close()
        self.tile.last_popup_close_time = 0.0
        self.tile.open_dropdown()

    def watch_cursor_and_outside_clicks(self):
        if QApplication.activeModalWidget() or QApplication.activePopupWidget():
            return

        cpos = QCursor.pos()
        my_geo = QRectF(self.geometry())
        in_popup = my_geo.contains(QPointF(cpos))

        all_tiles = self.tile.manager.get_all_tiles()
        hovered_tile = None

        for t in all_tiles:
            top_left = t.mapToGlobal(QPoint(0, 0))
            t_rect = QRectF(top_left.x(), top_left.y(), t.width(), t.height())
            if t_rect.contains(QPointF(cpos)):
                hovered_tile = t
                break

        if not in_popup and hovered_tile is None and is_any_mouse_button_down():
            self.close()
            if self.tile.manager.temp_topmost_active:
                self.tile.manager.deactivate_temp_topmost()
            return

        if self.tile.manager.dock_window:
            self.tile.manager.dock_window.update_wave_Targets(hovered_tile)

        if hovered_tile and hovered_tile is not self.tile:
            self._outside_ticks = 0
            if self._hovered_sibling is hovered_tile:
                self._sibling_dwell_ticks += 1
                if self._sibling_dwell_ticks >= 2:
                    self._hovered_sibling = None
                    self._sibling_dwell_ticks = 0
                    hovered_tile.last_popup_close_time = 0.0
                    hovered_tile.open_dropdown()
                    return
            else:
                self._hovered_sibling = hovered_tile
                self._sibling_dwell_ticks = 1
        else:
            self._hovered_sibling = None
            self._sibling_dwell_ticks = 0

            if self.settings.get("open_on_hover", False):
                padded_popup = my_geo.adjusted(-25, -25, 25, 25)
                tile_tl = self.tile.mapToGlobal(QPoint(0, 0))
                tile_rect = QRectF(tile_tl.x() - 15, tile_tl.y() - 15, self.tile.width() + 30, self.tile.height() + 30)
                if not padded_popup.contains(QPointF(cpos)) and not tile_rect.contains(QPointF(cpos)):
                    self._outside_ticks += 1
                    if self._outside_ticks >= 7:
                        self.close()
                else:
                    self._outside_ticks = 0

    def closeEvent(self, event):
        self.hover_watch_timer.stop()
        self.tile.last_popup_close_time = time.monotonic()
        if self.tile.popup is self:
            self.tile.popup = None
        if self.tile.manager.active_popup is self:
            self.tile.manager.active_popup = None
        if self.tile.manager.dock_window:
            self.tile.manager.dock_window.update_wave_Targets(None)
        super().closeEvent(event)

    def create_app_button(self, app_data, idx, item_width, icon_sz, font_sz, pad_v, is_grid=False):
        running = is_app_running(app_data, self.running_procs)
        btn = DraggableAppButton(
            self, app_data, idx, is_running=running, is_grid_mode=is_grid,
            item_w=item_width, icon_sz=icon_sz, font_sz=font_sz, pad_v=pad_v,
            accent_color=self.accent_color, is_light_bg=self.is_light_popup
        )
        btn.clicked.connect(lambda checked, a=app_data, b=btn: self.on_app_btn_clicked(a, b))
        btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        btn.customContextMenuRequested.connect(
            lambda pos, b=btn: self.show_item_menu(b.mapToGlobal(pos), b.index)
        )
        self.app_buttons.append(btn)
        return btn

    def on_app_btn_clicked(self, app_data, btn: DraggableAppButton):
        if btn.is_dragging_item or app_data.get("is_separator"):
            return
        self.launch_app(app_data)

    def toggle_grid_mode(self):
        cur = self.settings.get("popup_display_mode", "multicolumn")
        self.settings["popup_display_mode"] = "grid" if cur != "grid" else "multicolumn"
        self.tile.manager.save_config()
        self.close()
        self.tile.last_popup_close_time = 0.0
        self.tile.open_dropdown()

    def reorder_apps(self, from_idx, to_idx):
        if 0 <= from_idx < len(self.apps_list) and 0 <= to_idx < len(self.apps_list):
            item = self.apps_list.pop(from_idx)
            self.apps_list.insert(to_idx, item)
            self.tile.manager.save_config()
            self.close()
            self.tile.last_popup_close_time = 0.0
            self.tile.open_dropdown()

    def showEvent(self, event):
        super().showEvent(event)
        self.anim.start()

    def add_app_from_popup(self):
        self.close()
        self.tile.add_application()

    def add_folder_link_from_popup(self):
        self.close()
        self.tile.add_folder_link()

    def add_web_link_from_popup(self):
        self.close()
        self.tile.add_web_link()

    def launch_app(self, app_data):
        if app_data.get("is_separator"):
            return
        self.close()
        if self.tile.manager.temp_topmost_active:
            self.tile.manager.deactivate_temp_topmost()

        raw_p = app_data.get("path", "")
        if is_web_url(raw_p) or app_data.get("is_web"):
            webbrowser.open(normalize_web_url(raw_p))
            return

        fixed_p = smart_fix_path(raw_p, app_data.get("name", ""))
        if fixed_p:
            try:
                os.startfile(fixed_p)
                if not os.path.isdir(fixed_p):
                    QTimer.singleShot(1500, self.tile.manager.trigger_async_process_scan)
            except Exception as e:
                print(f"Launch error: {e}")

    def show_item_menu(self, global_pos, index):
        if not (0 <= index < len(self.apps_list)):
            return
        app_entry = self.apps_list[index]
        raw_p = app_entry.get("path", "")
        is_dir = os.path.isdir(raw_p) if raw_p else False
        is_web = is_web_url(raw_p) or app_entry.get("is_web", False)
        is_sep = app_entry.get("is_separator", False)

        pop_bg_hex = self.settings.get("popup_bg_color", "#181922")
        menu = QMenu(self)
        menu.setStyleSheet(get_menu_stylesheet(pop_bg_hex, self.accent_color))

        admin_act = None
        loc_act = None
        edit_url_act = None
        custom_ic_act = None

        if not is_sep:
            if is_web:
                edit_url_act = menu.addAction(get_menu_icon("web", pop_bg_hex), tr("ctx_edit_url"))
            else:
                if not is_dir:
                    admin_act = menu.addAction(get_menu_icon("admin", pop_bg_hex), tr("ctx_run_admin"))
                loc_act = menu.addAction(get_menu_icon("add_folder", pop_bg_hex), tr("ctx_open_loc"))

            custom_ic_act = menu.addAction(get_menu_icon("icon_pic", pop_bg_hex), tr("ctx_change_item_ic"))

        # Подменю отправки ярлыка в другую папку панели
        move_folder_actions = {}
        other_folders = [f for f in self.tile.manager.folders_data if f is not self.tile.data]
        if other_folders and not is_sep:
            send_menu = menu.addMenu(get_menu_icon("send_folder", pop_bg_hex), tr("ctx_move_to_folder"))
            for f_dict in other_folders:
                f_title = f_dict.get("title", tr("def_shortcut"))
                act = send_menu.addAction(get_menu_icon("add_folder", pop_bg_hex), f_title)
                move_folder_actions[act] = f_dict

        menu.addSeparator()
        ins_sep_act = menu.addAction(get_menu_icon("divider", pop_bg_hex), tr("ctx_add_sep_here"))
        sort_az_act = menu.addAction(get_menu_icon("sort", pop_bg_hex), tr("ctx_sort_az"))
        up_act = menu.addAction(get_menu_icon("up", pop_bg_hex), tr("ctx_move_up"))
        down_act = menu.addAction(get_menu_icon("down", pop_bg_hex), tr("ctx_move_down"))
        menu.addSeparator()
        rename_act = menu.addAction(get_menu_icon("rename", pop_bg_hex), tr("ctx_rename"))
        delete_act = menu.addAction(get_menu_icon("delete", pop_bg_hex), tr("ctx_delete_item"))

        action = menu.exec(global_pos)
        if not action:
            return

        if admin_act and action == admin_act:
            self.close()
            launch_as_admin(raw_p, app_entry.get("name", ""))
        elif loc_act and action == loc_act:
            self.close()
            open_file_location(raw_p, app_entry.get("name", ""))
        elif edit_url_act and action == edit_url_act:
            new_url, ok = QInputDialog.getText(None, tr("dlg_edit_url_t"), tr("dlg_edit_url_l"), text=raw_p)
            if ok and new_url.strip():
                app_entry["path"] = normalize_web_url(new_url)
                self.tile.manager.save_config()
        elif action in move_folder_actions:
            self.move_item_to_another_folder(index, move_folder_actions[action])
        elif action == ins_sep_act:
            self.add_separator_at(index + 1)
        elif action == sort_az_act:
            self.sort_apps_by_name()
        elif custom_ic_act and action == custom_ic_act:
            dlg = IconPickerDialog()
            if dlg.exec() == QDialog.DialogCode.Accepted and dlg.selected_icon:
                app_entry["custom_icon"] = dlg.selected_icon
                _ICON_CACHE.clear()
                self.tile.manager.save_config()
                self.close()
                self.tile.last_popup_close_time = 0.0
                self.tile.open_dropdown()
        elif action == delete_act:
            self.tile.remove_app(index)
            self.close()
        elif action == rename_act:
            self.tile.rename_app(index)
            self.close()
        elif action == up_act and index > 0:
            self.reorder_apps(index, index - 1)
        elif action == down_act and index < len(self.apps_list) - 1:
            self.reorder_apps(index, index + 1)


class FolderTile(QWidget):
    def __init__(self, manager, folder_data, parent=None, is_standalone=False):
        super().__init__(parent)
        self.manager = manager
        self.data = folder_data
        self.is_standalone = is_standalone
        self.is_hovered = False
        self.is_pressed = False
        self.popup = None
        self.last_popup_close_time = 0.0
        self.suppress_next_open = False
        self._resolved_img_path = ""
        self._favicon_workers = []

        self.anim_scale = 1.0
        self.target_scale = 1.0
        self.scale_vel = 0.0
        self.anim_offset_y = 0.0
        self.target_offset_y = 0.0
        self.offset_vel = 0.0
        self.anim_angle = 0.0
        self.anim_glow = 0.0
        self.anim_phase = 0.0

        self.setAcceptDrops(True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        if self.is_standalone:
            self.apply_standalone_flags()

        self.hover_open_timer = QTimer(self)
        self.hover_open_timer.setSingleShot(True)
        self.hover_open_timer.timeout.connect(self.on_hover_timeout)

        # Таймер долгого удержания ЛКМ (420 мс) для автоматического включения режима перетаскивания папок!
        self.long_press_timer = QTimer(self)
        self.long_press_timer.setSingleShot(True)
        self.long_press_timer.timeout.connect(self.on_long_press_triggered)

        self.drag_start_pos = None
        self.is_dragging = False
        self.update_appearance()

        if self.is_standalone:
            self.move(self.data.get("x", 100), self.data.get("y", 100))
            self.show()

    def on_long_press_triggered(self):
        """Если пользователь зажал ЛКМ на папке на 0.42 сек — сразу включаем режим перемещения папок!"""
        if self.is_pressed and not self.manager.edit_mode:
            self.suppress_next_open = True
            self.manager.toggle_edit_mode(True)

    def apply_standalone_flags(self):
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        if self.manager.settings.get("always_on_top", False) or self.manager.temp_topmost_active:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)

    def update_appearance(self):
        size = self.data.get("size", 88)
        raw_img = self.data.get("image_path", "")
        if not raw_img and self.data.get("is_favorites"):
            raw_img = find_app_icon_path()
        self._resolved_img_path = resolve_image_path(raw_img)
        self.setFixedSize(size + 26, size + 26)
        self.update()

    def enterEvent(self, event):
        self.is_hovered = True
        if self.manager.dock_window and not self.is_standalone:
            self.manager.dock_window.update_wave_Targets(self)
        else:
            self.update()

        if self.manager.settings.get("open_on_hover", False) and not self.manager.edit_mode:
            delay = 30 if (self.manager.active_popup and self.manager.active_popup.isVisible()) else 140
            self.hover_open_timer.start(delay)

    def leaveEvent(self, event):
        self.is_hovered = False
        self.is_pressed = False
        self.hover_open_timer.stop()
        self.long_press_timer.stop()
        if self.manager.dock_window and not self.is_standalone:
            self.manager.dock_window.update_wave_Targets(None)
        else:
            self.update()

    def on_hover_timeout(self):
        if self.manager.edit_mode or not self.is_hovered or not self.manager.settings.get("open_on_hover", False):
            return
        if QApplication.activePopupWidget() or QApplication.activeModalWidget():
            return
        if self.popup and self.popup.isVisible():
            return
        self.last_popup_close_time = 0.0
        self.open_dropdown()

    def has_running_apps(self):
        if not self.manager.settings.get("show_running_indicator", True):
            return False
        running_set = self.manager.running_procs
        if not running_set:
            return False
        return any(is_app_running(a, running_set) for a in self.data.get("apps", []))

    def draw_favorites_star_glyph(self, painter, center_x, top_y, icon_size, accent_hex):
        painter.save()
        self.draw_default_folder_glyph(painter, center_x, top_y, icon_size, accent_hex)
        star_font = QFont("Segoe UI Symbol", max(10, int(icon_size * 0.36)))
        painter.setFont(star_font)
        painter.setPen(QColor(35, 28, 10, 220))
        star_rect = QRectF(center_x - icon_size / 2, top_y + icon_size * 0.14, icon_size, icon_size * 0.65)
        painter.drawText(star_rect, Qt.AlignmentFlag.AlignCenter, "★")
        painter.restore()

    def draw_default_folder_glyph(self, painter, center_x, top_y, icon_size, accent_hex):
        painter.save()
        w = icon_size
        h = icon_size * 0.78
        x = center_x - w / 2
        y = top_y

        c_back = QColor(accent_hex)
        c_back.setAlpha(150)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(c_back)
        painter.drawRoundedRect(QRectF(x, y + 3, w * 0.42, 10), 3, 3)

        grad = QLinearGradient(x, y + 8, x, y + h)
        c_top = QColor(accent_hex).lighter(115)
        c_bot = QColor(accent_hex).darker(115)
        c_top.setAlpha(235)
        c_bot.setAlpha(235)
        grad.setColorAt(0, c_top)
        grad.setColorAt(1, c_bot)

        painter.setBrush(grad)
        painter.drawRoundedRect(QRectF(x, y + 8, w, h - 8), 5, 5)

        painter.setPen(QPen(QColor(255, 255, 255, 90), 1))
        painter.drawLine(int(x + 4), int(y + 9), int(x + w - 4), int(y + 9))
        painter.restore()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        rect = QRectF(self.rect()).adjusted(13, 13, -13, -13)
        size = rect.width()

        is_fav = self.data.get("is_favorites", False)
        c1_hex, c2_hex, accent_hex = get_tile_colors(self.data)
        anim_style = self.manager.settings.get("animation_style", "wave")

        if anim_style == "float_up" and self.anim_glow > 0.05:
            glow_w = size * 0.48 * self.anim_glow
            glow_rect = QRectF(rect.center().x() - glow_w / 2, rect.bottom() + 4, glow_w, 3)
            g_col = QColor(accent_hex)
            g_col.setAlpha(int(210 * min(1.0, self.anim_glow)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(g_col)
            painter.drawRoundedRect(glow_rect, 1.5, 1.5)

        cx, cy = rect.center().x(), rect.center().y()
        painter.translate(cx, cy + self.anim_offset_y)
        if abs(self.anim_angle) > 0.05:
            painter.rotate(self.anim_angle)
        painter.scale(self.anim_scale, self.anim_scale)
        painter.translate(-cx, -cy)

        icon_only = self.data.get("icon_only", False)
        show_title = self.data.get("show_title", True)

        if not icon_only:
            shadow_rect = rect.adjusted(1, 2, 1, 2)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 0, 0, 85))
            painter.drawRoundedRect(shadow_rect, 16, 16)

            grad = QLinearGradient(rect.topLeft(), rect.bottomLeft())
            c1 = QColor(c1_hex)
            c2 = QColor(c2_hex)
            c1.setAlpha(242 if self.is_hovered else 215)
            c2.setAlpha(250 if self.is_hovered else 230)
            grad.setColorAt(0, c1)
            grad.setColorAt(1, c2)
            painter.setBrush(grad)

            if self.manager.edit_mode:
                border_pen = QPen(QColor("#F6AD55"), 2.0 if self.is_dragging else 1.8, Qt.PenStyle.DashLine)
            elif self.is_hovered:
                pen_w = 1.8 + (0.8 * self.anim_glow if anim_style == "pulse" else 0.0)
                border_pen = QPen(QColor(accent_hex), pen_w)
            else:
                border_pen = QPen(QColor(255, 255, 255, 42), 1.0)
            painter.setPen(border_pen)
            painter.drawRoundedRect(rect, 16, 16)
        else:
            if self.manager.edit_mode:
                painter.setPen(QPen(QColor("#F6AD55"), 1.6, Qt.PenStyle.DashLine))
                painter.setBrush(QColor(255, 255, 255, 18))
                painter.drawRoundedRect(rect, 16, 16)
            elif self.is_hovered:
                painter.setPen(QPen(QColor(accent_hex), 1.3))
                painter.setBrush(QColor(255, 255, 255, 22))
                painter.drawRoundedRect(rect, 16, 16)

        if self._resolved_img_path:
            base_ratio = (0.76 if show_title else 0.92) if icon_only else (0.64 if show_title else 0.82)
            icon_box_h = size * base_ratio
            master_pix = get_master_folder_pixmap(self._resolved_img_path)
            if not master_pix.isNull():
                pw, ph = master_pix.width(), master_pix.height()
                scale_f = min(icon_box_h / pw, icon_box_h / ph)
                draw_w, draw_h = pw * scale_f, ph * scale_f
                px = rect.left() + (size - draw_w) / 2.0
                if show_title:
                    avail_h = size * (0.75 if icon_only else 0.70)
                    py = rect.top() + (avail_h - draw_h) / 2.0
                else:
                    py = rect.top() + (size - draw_h) / 2.0
                painter.drawPixmap(QRectF(px, py, draw_w, draw_h), master_pix, QRectF(master_pix.rect()))
        else:
            glyph_size = size * 0.44 if show_title else size * 0.55
            top_offset = rect.top() + (size * 0.16 if show_title else size * 0.25)
            if is_fav:
                self.draw_favorites_star_glyph(painter, rect.center().x(), top_offset, glyph_size, accent_hex)
            else:
                self.draw_default_folder_glyph(painter, rect.center().x(), top_offset, glyph_size, accent_hex)

        if self.has_running_apps():
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(72, 187, 120, 90))
            painter.drawEllipse(int(rect.left() + 6), int(rect.top() + 5), 11, 11)
            painter.setBrush(QColor("#48BB78"))
            painter.drawEllipse(int(rect.left() + 8), int(rect.top() + 7), 7, 7)

        # Считаем только реальные элементы (без разделителей)
        real_apps = [a for a in self.data.get("apps", []) if not a.get("is_separator")]
        app_count = len(real_apps)
        if app_count > 0 and self.data.get("show_badge", True):
            badge_rect = QRectF(rect.right() - 22, rect.top() + 4, 18, 15)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(20, 22, 30, 195) if icon_only else QColor(255, 255, 255, 35))
            painter.drawRoundedRect(badge_rect, 7, 7)

            painter.setPen(QColor(255, 255, 255, 220))
            painter.setFont(QFont("Segoe UI", 8, QFont.Weight.DemiBold))
            painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, str(app_count))

        if show_title:
            text_rect = QRectF(rect.left() + 1, rect.bottom() - size * 0.28, size - 2, size * 0.26)
            custom_font_sz = self.data.get("title_font_size", 0)
            font_size = custom_font_sz if (custom_font_sz and custom_font_sz > 0) else max(8, min(11, int(size / 8.5)))

            painter.setFont(QFont("Segoe UI", font_size, QFont.Weight.DemiBold))

            elided_text = painter.fontMetrics().elidedText(
                self.data.get("title", tr("def_shortcut")), Qt.TextElideMode.ElideRight, int(text_rect.width())
            )
            painter.setPen(QColor(0, 0, 0, 200))
            painter.drawText(text_rect.adjusted(1, 1, 1, 1), Qt.AlignmentFlag.AlignCenter, elided_text)
            painter.setPen(QColor("#FEF08A") if is_fav else QColor(250, 252, 255))
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, elided_text)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            self.is_hovered = True
            self.update()
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.is_hovered = False
        self.update()

    def dropEvent(self, event):
        self.is_hovered = False
        valid_img_exts = (".png", ".ico", ".webp", ".jpg", ".jpeg", ".bmp", ".svg")

        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_path = os.path.normpath(url.toLocalFile())
                    if file_path:
                        # При перетаскивании изображения спрашиваем: Сделать иконкой папки или добавить в список?
                        if not os.path.isdir(file_path) and file_path.lower().endswith(valid_img_exts) and os.path.exists(file_path):
                            fname = os.path.basename(file_path)
                            reply = QMessageBox.question(
                                None,
                                tr("dlg_img_drop_t"),
                                tr("dlg_img_drop_q").format(fname),
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                                QMessageBox.StandardButton.Yes
                            )
                            if reply == QMessageBox.StandardButton.Cancel:
                                continue
                            elif reply == QMessageBox.StandardButton.Yes:
                                try:
                                    dest = os.path.join(ICONS_DIR, fname)
                                    if os.path.abspath(file_path) != os.path.abspath(dest):
                                        shutil.copy2(file_path, dest)
                                    self.data["image_path"] = os.path.join("icons", fname)
                                except Exception:
                                    self.data["image_path"] = file_path
                                self.update_appearance()
                                continue

                        base_name = os.path.basename(file_path.rstrip("\\/"))
                        if not os.path.isdir(file_path):
                            base_name = os.path.splitext(base_name)[0]
                        clean_name = base_name.replace(" — ярлык", "").replace(" - Ярлык", "").replace(" - Shortcut", "")
                        new_entry = {"name": clean_name or file_path, "path": file_path}
                        self.data.setdefault("apps", []).append(new_entry)
                else:
                    web_url = url.toString()
                    self._register_web_entry(web_url)
        elif event.mimeData().hasText():
            txt = event.mimeData().text().strip()
            if txt.startswith(("http://", "https://", "192.168.", "10.", "127.0.", "localhost")):
                self._register_web_entry(normalize_web_url(txt))

        self.update()
        self.manager.save_config()
        self.manager.start_background_warmer()
        event.acceptProposedAction()

    def _register_web_entry(self, web_url: str, custom_title: str = ""):
        web_url = normalize_web_url(web_url)
        parsed = urllib.parse.urlparse(web_url)
        host_label = custom_title or parsed.netloc or web_url
        new_entry = {"name": host_label, "path": web_url, "is_web": True, "exe_name": ""}
        self.data.setdefault("apps", []).append(new_entry)

        safe_host = re.sub(r'[^a-zA-Z0-9_.-]', '_', parsed.hostname or "web")
        fav_file = os.path.join(USER_ICONS_DIR, f"fav_{safe_host}.png")
        worker = FaviconDownloaderThread(web_url, fav_file)
        worker.favicon_ready.connect(lambda u, p, entry=new_entry: self._on_favicon_downloaded(entry, p))
        self._favicon_workers.append(worker)
        worker.start()

    def _on_favicon_downloaded(self, app_entry: dict, saved_icon_path: str):
        if os.path.exists(saved_icon_path):
            app_entry["custom_icon"] = os.path.join("icons", os.path.basename(saved_icon_path))
            _ICON_CACHE.clear()
            self.manager.save_config()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.hover_open_timer.stop()
            self.long_press_timer.stop()
            if self.manager.active_popup and self.manager.active_popup.isVisible():
                self.manager.active_popup.close()
            self.manager.show_context_menu(self, event.globalPosition().toPoint())
            event.accept()
            return

        if event.button() == Qt.MouseButton.LeftButton:
            self.hover_open_timer.stop()
            self.is_pressed = True
            self.drag_start_pos = event.globalPosition().toPoint()
            self.is_dragging = False

            # Запускаем таймер долгого нажатия ЛКМ (420 мс) для включения перемещения папок!
            if not self.manager.edit_mode:
                self.long_press_timer.start(420)

            if self.manager.dock_window and not self.is_standalone:
                self.manager.dock_window.update_wave_Targets(self, pressed=True)

            just_closed = (time.monotonic() - self.last_popup_close_time) < 0.25
            currently_open = (self.popup is not None and self.popup.isVisible())
            if currently_open:
                self.popup.close()
                self.suppress_next_open = True
            elif just_closed:
                self.suppress_next_open = True
            else:
                self.suppress_next_open = False

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton and self.drag_start_pos:
            cur_global = event.globalPosition().toPoint()
            dist = (cur_global - self.drag_start_pos).manhattanLength()
            if dist > 6:
                self.long_press_timer.stop()
                if not self.manager.edit_mode:
                    return
                self.is_dragging = True

                if not self.is_standalone and self.manager.dock_window and not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                    mode = self.manager.settings.get("layout_mode", "dock_horizontal")
                    for other_tile in list(self.manager.dock_window.tiles):
                        if other_tile is self:
                            continue
                        tl = other_tile.mapToGlobal(QPoint(0, 0))
                        if mode == "dock_horizontal":
                            hit = (tl.x() <= cur_global.x() <= tl.x() + other_tile.width())
                        else:
                            hit = (tl.y() <= cur_global.y() <= tl.y() + other_tile.height())

                        if hit:
                            idx1 = self.manager.folders_data.index(self.data)
                            idx2 = self.manager.folders_data.index(other_tile.data)
                            self.manager.folders_data[idx1], self.manager.folders_data[idx2] = (
                                self.manager.folders_data[idx2], self.manager.folders_data[idx1]
                            )
                            self.manager.dock_window.swap_tile_widgets(idx1, idx2)
                            self.drag_start_pos = cur_global
                            break
                    return

                diff = cur_global - self.drag_start_pos
                target_window = self if self.is_standalone else self.window()
                target_window.move(target_window.pos() + diff)
                self.drag_start_pos = cur_global

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.long_press_timer.stop()
            self.is_pressed = False
            if self.manager.dock_window and not self.is_standalone:
                self.manager.dock_window.update_wave_Targets(self if self.is_hovered else None)

            if self.is_dragging:
                if self.is_standalone or (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                    target_window = self if self.is_standalone else self.window()
                    if self.manager.settings.get("snap_to_grid", True):
                        snapped_x = round(target_window.x() / 10) * 10
                        snapped_y = round(target_window.y() / 10) * 10
                        target_window.move(snapped_x, snapped_y)

                    if self.is_standalone:
                        self.data["x"] = self.x()
                        self.data["y"] = self.y()
                    else:
                        self.manager.settings["dock_x"] = target_window.x()
                        self.manager.settings["dock_y"] = target_window.y()
                        if hasattr(target_window, "update_docked_edge"):
                            target_window.update_docked_edge()
                self.manager.save_config()
            else:
                if self.manager.edit_mode and not self.suppress_next_open:
                    self.manager.toggle_edit_mode(False)
                elif not self.manager.edit_mode and not self.suppress_next_open:
                    self.open_dropdown()
            self.drag_start_pos = None
            self.is_dragging = False
            self.suppress_next_open = False
            self.update()

    def open_dropdown(self):
        if self.manager.active_popup and self.manager.active_popup.isVisible():
            if self.manager.active_popup.tile is self:
                return
            self.manager.active_popup.close()

        mode = self.manager.settings.get("layout_mode", "dock_horizontal")
        direction = "side" if mode == "dock_vertical" else "down"

        self.popup = DropdownPopup(self, open_direction=direction, running_procs=self.manager.running_procs)
        self.manager.active_popup = self.popup
        self.popup.adjustSize()

        screen_geo = QApplication.primaryScreen().availableGeometry()
        global_top_left = self.mapToGlobal(QPoint(0, 0))

        if direction == "side":
            x = global_top_left.x() + self.width() + 2
            y = global_top_left.y() - 6
            if x + self.popup.width() > screen_geo.right():
                x = global_top_left.x() - self.popup.width() - 2
            if y + self.popup.height() > screen_geo.bottom():
                y = screen_geo.bottom() - self.popup.height() - 10
        else:
            x = global_top_left.x() - 4
            y = global_top_left.y() + self.height() - 2
            if y + self.popup.height() > screen_geo.bottom():
                y = global_top_left.y() - self.popup.height() + 2
            if x + self.popup.width() > screen_geo.right():
                x = screen_geo.right() - self.popup.width() - 10

        self.popup.move(max(5, x), max(5, y))
        self.popup.show()
        self.popup.raise_()

    def contextMenuEvent(self, event):
        event.accept()

    def add_application(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            tr("dlg_pick_app"),
            os.path.expanduser("~\\Desktop"),
            tr("app_filter"),
            options=QFileDialog.Option.DontResolveSymlinks
        )
        if file_path:
            file_path = os.path.normpath(file_path)
            default_name = (
                os.path.splitext(os.path.basename(file_path))[0]
                .replace(" — ярлык", "")
                .replace(" - Ярлык", "")
                .replace(" - Shortcut", "")
            )
            name, ok = QInputDialog.getText(
                self, tr("dlg_app_name_t"), tr("dlg_app_name_l"), text=default_name
            )
            if ok and name:
                new_entry = {"name": name, "path": file_path}
                self.data.setdefault("apps", []).append(new_entry)
                self.update()
                self.manager.save_config()
                self.manager.start_background_warmer()

    def add_folder_link(self):
        dir_path = QFileDialog.getExistingDirectory(
            self,
            tr("dlg_pick_dir"),
            os.path.expanduser("~")
        )
        if dir_path:
            dir_path = os.path.normpath(dir_path)
            default_name = os.path.basename(dir_path.rstrip("\\/")) or dir_path
            name, ok = QInputDialog.getText(
                self, tr("dlg_dir_name_t"), tr("dlg_dir_name_l"), text=default_name
            )
            if ok and name:
                new_entry = {"name": name, "path": dir_path, "is_dir": True, "exe_name": ""}
                self.data.setdefault("apps", []).append(new_entry)
                self.update()
                self.manager.save_config()

    def add_web_link(self):
        raw_url, ok = QInputDialog.getText(
            None,
            tr("dlg_web_t"),
            tr("dlg_web_l")
        )
        if ok and raw_url.strip():
            full_url = normalize_web_url(raw_url)
            parsed = urllib.parse.urlparse(full_url)
            default_title = parsed.netloc or raw_url.strip()
            name, ok2 = QInputDialog.getText(
                None,
                tr("dlg_web_name_t"),
                tr("dlg_web_name_l"),
                text=default_title
            )
            if ok2 and name.strip():
                self._register_web_entry(full_url, name.strip())
                self.update()
                self.manager.save_config()

    def remove_app(self, index):
        apps = self.data.get("apps", [])
        if 0 <= index < len(apps):
            apps.pop(index)
            self.update()
            self.manager.save_config()

    def rename_app(self, index):
        apps = self.data.get("apps", [])
        if 0 <= index < len(apps):
            old_name = apps[index]["name"]
            new_name, ok = QInputDialog.getText(self, tr("ctx_rename"), tr("dlg_rename_l"), text=old_name)
            if ok is not None and ok:
                apps[index]["name"] = new_name
                self.manager.save_config()


class DockPanelWindow(QWidget):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.tiles = []
        self.is_hidden_at_edge = False
        self.docked_edge = None
        self.hovered_tile_ref = None
        self.wiggle_tick = 0.0

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.apply_window_flags()

        self.drag_start_pos = None
        self.pos_anim = QPropertyAnimation(self, b"pos")
        self.pos_anim.setDuration(180)
        self.pos_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.wave_timer = QTimer(self)
        self.wave_timer.setInterval(16)
        self.wave_timer.timeout.connect(self.step_wave_animation)

        self.rebuild_panel()

        self.move(
            self.manager.settings.get("dock_x", 260),
            self.manager.settings.get("dock_y", 40)
        )
        self.show()
        self.update_docked_edge()

        self.edge_timer = QTimer(self)
        self.edge_timer.timeout.connect(self.check_auto_hide)
        self.edge_timer.start(250)

    def center_on_screen(self):
        """Выравнивает панель идеально по центру экрана"""
        screen_geo = QApplication.primaryScreen().availableGeometry()
        mode = self.manager.settings.get("layout_mode", "dock_horizontal")
        if mode == "dock_horizontal":
            new_x = screen_geo.left() + (screen_geo.width() - self.width()) // 2
            new_y = self.y()
            new_y = max(screen_geo.top() + 5, min(new_y, screen_geo.bottom() - self.height() - 5))
        else:
            new_x = self.x()
            new_y = screen_geo.top() + (screen_geo.height() - self.height()) // 2
            new_x = max(screen_geo.left() + 5, min(new_x, screen_geo.right() - self.width() - 5))

        self.move(new_x, new_y)
        self.manager.settings["dock_x"] = new_x
        self.manager.settings["dock_y"] = new_y
        self.update_docked_edge()
        self.manager.save_config()

    def apply_window_flags(self):
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        if (
            self.manager.settings.get("always_on_top", False)
            or self.manager.settings.get("auto_hide", False)
            or self.manager.temp_topmost_active
        ):
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)

    def swap_tile_widgets(self, idx1: int, idx2: int):
        self.tiles[idx1], self.tiles[idx2] = self.tiles[idx2], self.tiles[idx1]
        lay = self.layout()
        if lay:
            for t in self.tiles:
                lay.removeWidget(t)
            for t in self.tiles:
                lay.addWidget(t)
        self.update()

    def update_wave_Targets(self, hovered_tile, pressed=False):
        self.hovered_tile_ref = hovered_tile
        style = self.manager.settings.get("animation_style", "wave")
        if not self.manager.settings.get("hover_animation", True) or style == "none" or hovered_tile is None:
            for t in self.tiles:
                t.target_scale = 1.0
                t.target_offset_y = 0.0
        else:
            try:
                h_idx = self.tiles.index(hovered_tile)
            except ValueError:
                h_idx = -1

            for idx, t in enumerate(self.tiles):
                if idx == h_idx:
                    if style == "wave":
                        t.target_scale = 1.13 if pressed else 1.10
                        t.target_offset_y = 3.5 if pressed else 2.5
                    elif style == "float_up":
                        t.target_scale = 1.10 if pressed else 1.08
                        t.target_offset_y = -2.0 if pressed else -5.5
                    elif style == "spring":
                        t.target_scale = 1.15 if pressed else 1.12
                        t.target_offset_y = 2.0 if pressed else -3.0
                    elif style == "pulse":
                        t.target_scale = 1.08
                        t.target_offset_y = 0.0
                    elif style == "zoom_only":
                        t.target_scale = 1.14 if pressed else 1.11
                        t.target_offset_y = 0.0
                    elif style == "tilt":
                        t.target_scale = 1.09
                        t.target_offset_y = -2.0
                        if t.anim_phase == 0.0:
                            t.anim_phase = 0.1
                elif abs(idx - h_idx) == 1 and style == "wave":
                    t.target_scale = 0.92
                    t.target_offset_y = -1.0
                elif abs(idx - h_idx) == 2 and style == "wave":
                    t.target_scale = 0.96
                    t.target_offset_y = 0.0
                else:
                    t.target_scale = 1.0
                    t.target_offset_y = 0.0

        if not self.wave_timer.isActive():
            self.wave_timer.start()

    def reset_wave_targets(self):
        self.hovered_tile_ref = None
        for t in self.tiles:
            t.target_scale = 1.0
            t.target_offset_y = 0.0
            t.anim_angle = 0.0
            t.anim_glow = 0.0
        if not self.wave_timer.isActive():
            self.wave_timer.start()

    def step_wave_animation(self):
        still_moving = False
        style = self.manager.settings.get("animation_style", "wave")
        edit_mode = self.manager.edit_mode

        if edit_mode:
            self.wiggle_tick += 0.26
            still_moving = True

        for idx, t in enumerate(self.tiles):
            is_h = (t is self.hovered_tile_ref)

            if edit_mode:
                t.anim_angle = 3.2 * math.sin(self.wiggle_tick + idx * 1.1)
                t.anim_offset_y = 1.2 * math.cos(self.wiggle_tick * 1.2 + idx * 0.9)
                t.anim_scale = 1.06 if (is_h or t.is_dragging) else 0.98
                t.update()
                continue

            if style == "pulse" and is_h:
                t.anim_phase += 0.14
                t.target_scale = 1.07 + 0.04 * math.sin(t.anim_phase)
                t.anim_glow = 0.5 + 0.5 * math.sin(t.anim_phase)
                still_moving = True
            elif style == "float_up" and is_h:
                t.anim_glow = min(1.0, t.anim_glow + 0.18)
            else:
                if t.anim_glow > 0.01:
                    t.anim_glow = max(0.0, t.anim_glow - 0.15)
                    still_moving = True
                else:
                    t.anim_glow = 0.0

            if style == "tilt" and is_h and t.anim_phase > 0.0:
                t.anim_phase += 0.25
                t.anim_angle = 7.5 * math.sin(t.anim_phase) * math.exp(-0.18 * t.anim_phase)
                if t.anim_phase < 18.0:
                    still_moving = True
                else:
                    t.anim_angle = 0.0
            else:
                t.anim_phase = 0.0 if not is_h else t.anim_phase
                if abs(t.anim_angle) > 0.1:
                    t.anim_angle *= 0.72
                    still_moving = True
                else:
                    t.anim_angle = 0.0

            if style == "spring":
                stiffness = 0.28
                damping = 0.68
                t.scale_vel = (t.scale_vel + (t.target_scale - t.anim_scale) * stiffness) * damping
                t.offset_vel = (t.offset_vel + (t.target_offset_y - t.anim_offset_y) * stiffness) * damping
                t.anim_scale += t.scale_vel
                t.anim_offset_y += t.offset_vel
                if abs(t.scale_vel) > 0.001 or abs(t.target_scale - t.anim_scale) > 0.002 or abs(t.offset_vel) > 0.05:
                    t.update()
                    still_moving = True
                else:
                    t.anim_scale = t.target_scale
                    t.anim_offset_y = t.target_offset_y
                    t.update()
            else:
                speed = 0.30
                ds = t.target_scale - t.anim_scale
                dy = t.target_offset_y - t.anim_offset_y
                if abs(ds) > 0.002 or abs(dy) > 0.06 or still_moving:
                    t.anim_scale += ds * speed
                    t.anim_offset_y += dy * speed
                    t.update()
                    if abs(ds) > 0.002 or abs(dy) > 0.06:
                        still_moving = True
                else:
                    if t.anim_scale != t.target_scale or t.anim_offset_y != t.target_offset_y:
                        t.anim_scale = t.target_scale
                        t.anim_offset_y = t.target_offset_y
                        t.update()

        if not still_moving:
            self.wave_timer.stop()

    def update_margins_and_repaint(self):
        lay = self.layout()
        if lay:
            mode = self.manager.settings.get("layout_mode", "dock_horizontal")
            shape = self.manager.settings.get("dock_shape", "rounded")
            slant = self.manager.settings.get("dock_slant", 24)
            extra_side = int(slant * 0.78) if shape in ("hexagon", "trapezoid_up", "trapezoid_down", "chamfer") else 0
            if mode == "dock_horizontal":
                lay.setContentsMargins(12 + extra_side, 8, 12 + extra_side, 8)
            else:
                lay.setContentsMargins(8, 12 + extra_side, 8, 12 + extra_side)
        self.adjustSize()
        self.update()

    def rebuild_panel(self):
        if self.layout():
            while self.layout().count():
                item = self.layout().takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            QWidget().setLayout(self.layout())

        self.tiles.clear()
        mode = self.manager.settings.get("layout_mode", "dock_horizontal")

        layout = QVBoxLayout(self) if mode == "dock_vertical" else QHBoxLayout(self)
        layout.setSpacing(0)
        layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetFixedSize)

        for f_data in self.manager.folders_data:
            tile = FolderTile(self.manager, f_data, parent=self, is_standalone=False)
            layout.addWidget(tile)
            self.tiles.append(tile)

        self.update_margins_and_repaint()
        if self.manager.edit_mode and not self.wave_timer.isActive():
            self.wave_timer.start()

    def update_docked_edge(self):
        screen = QApplication.primaryScreen().geometry()
        x, y = self.x(), self.y()
        w, h = self.width(), self.height()
        snap_dist = 35

        if x <= screen.left() + snap_dist:
            self.docked_edge = "left"
        elif x + w >= screen.right() - snap_dist:
            self.docked_edge = "right"
        elif y <= screen.top() + snap_dist:
            self.docked_edge = "top"
        elif y + h >= screen.bottom() - snap_dist:
            self.docked_edge = "bottom"
        else:
            self.docked_edge = None
            self.is_hidden_at_edge = False

    def check_auto_hide(self):
        if not self.manager.settings.get("auto_hide", False) or self.manager.edit_mode or self.manager.temp_topmost_active:
            if self.is_hidden_at_edge:
                self.slide_to_visible()
            return

        if (self.manager.active_popup and self.manager.active_popup.isVisible()) or QApplication.activePopupWidget() or QApplication.activeModalWidget():
            return

        self.update_docked_edge()
        if not self.docked_edge:
            return

        cursor_pos = QCursor.pos()
        geo = self.geometry()
        peek_px = 5

        if not self.is_hidden_at_edge:
            if not geo.adjusted(-18, -18, 18, 18).contains(cursor_pos):
                self.slide_to_hidden(peek_px)
        else:
            if geo.adjusted(-8, -8, 8, 8).contains(cursor_pos):
                self.slide_to_visible()

    def slide_to_hidden(self, peek_px=5):
        screen = QApplication.primaryScreen().geometry()
        base_x = self.manager.settings.get("dock_x", self.x())
        base_y = self.manager.settings.get("dock_y", self.y())
        target = QPoint(base_x, base_y)

        if self.docked_edge == "left":
            target.setX(screen.left() - self.width() + peek_px)
        elif self.docked_edge == "right":
            target.setX(screen.right() - peek_px)
        elif self.docked_edge == "top":
            target.setY(screen.top() - self.height() + peek_px)
        elif self.docked_edge == "bottom":
            target.setY(screen.bottom() - peek_px)

        self.is_hidden_at_edge = True
        self.pos_anim.stop()
        self.pos_anim.setStartValue(self.pos())
        self.pos_anim.setEndValue(target)
        self.pos_anim.start()
        self.update()

    def slide_to_visible(self):
        screen = QApplication.primaryScreen().geometry()
        base_x = self.manager.settings.get("dock_x", self.x())
        base_y = self.manager.settings.get("dock_y", self.y())

        if self.docked_edge == "left":
            base_x = screen.left() + 2
        elif self.docked_edge == "right":
            base_x = screen.right() - self.width() - 2
        elif self.docked_edge == "top":
            base_y = screen.top() + 2
        elif self.docked_edge == "bottom":
            base_y = screen.bottom() - self.height() - 2

        self.is_hidden_at_edge = False
        self.pos_anim.stop()
        self.pos_anim.setStartValue(self.pos())
        self.pos_anim.setEndValue(QPoint(base_x, base_y))
        self.pos_anim.start()
        self.update()

    def build_dock_path(self, rect: QRectF) -> QPainterPath:
        shape = self.manager.settings.get("dock_shape", "rounded")
        s = float(self.manager.settings.get("dock_slant", 24))
        corner_r = float(self.manager.settings.get("dock_corner_radius", 14))
        mode = self.manager.settings.get("layout_mode", "dock_horizontal")

        path = QPainterPath()
        L, T, R, B = rect.left(), rect.top(), rect.right(), rect.bottom()
        W, H = rect.width(), rect.height()

        if shape == "rounded":
            path.addRoundedRect(rect, s, s)
            return path

        if shape == "rect":
            pts = [QPointF(L, T), QPointF(R, T), QPointF(R, B), QPointF(L, B)]
            return build_rounded_polygon_path(pts, corner_r)

        if shape == "chamfer":
            c = min(s, W / 3, H / 3)
            pts = [
                QPointF(L + c, T), QPointF(R - c, T),
                QPointF(R, T + c), QPointF(R, B - c),
                QPointF(R - c, B), QPointF(L + c, B),
                QPointF(L, B - c), QPointF(L, T + c)
            ]
            return build_rounded_polygon_path(pts, corner_r * 0.5)

        if mode == "dock_horizontal":
            s = min(s, W / 4)
            if shape == "hexagon":
                mid_y = (T + B) / 2.0
                pts = [
                    QPointF(L + s, T),
                    QPointF(R - s, T),
                    QPointF(R, mid_y),
                    QPointF(R - s, B),
                    QPointF(L + s, B),
                    QPointF(L, mid_y)
                ]
            elif shape == "trapezoid_up":
                pts = [
                    QPointF(L, T),
                    QPointF(R, T),
                    QPointF(R - s, B),
                    QPointF(L + s, B)
                ]
            elif shape == "trapezoid_down":
                pts = [
                    QPointF(L + s, T),
                    QPointF(R - s, T),
                    QPointF(R, B),
                    QPointF(L, B)
                ]
            else:
                path.addRoundedRect(rect, 22, 22)
                return path
        else:
            s = min(s, H / 4)
            if shape == "hexagon":
                mid_x = (L + R) / 2.0
                pts = [
                    QPointF(mid_x, T),
                    QPointF(R, T + s),
                    QPointF(R, B - s),
                    QPointF(mid_x, B),
                    QPointF(L, B - s),
                    QPointF(L, T + s)
                ]
            elif shape == "trapezoid_up":
                pts = [
                    QPointF(L, T),
                    QPointF(R, T + s),
                    QPointF(R, B - s),
                    QPointF(L, B)
                ]
            else:
                pts = [
                    QPointF(L, T + s),
                    QPointF(R, T),
                    QPointF(R, B),
                    QPointF(L, B - s)
                ]

        return build_rounded_polygon_path(pts, corner_r)

    def paintEvent(self, event):
        if not self.manager.settings.get("show_dock_bg", True) and not self.is_hidden_at_edge:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(2, 2, -2, -2)

        if self.is_hidden_at_edge:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(96, 205, 255, 190))
            painter.drawRoundedRect(rect, 6, 6)
            return

        bg_alpha = self.manager.settings.get("dock_bg_opacity", 175)
        border_alpha = self.manager.settings.get("dock_border_opacity", 65)
        use_accent = self.manager.settings.get("dock_accent_border", False)
        base_col = QColor(self.manager.settings.get("dock_bg_color", "#12131A"))

        accent_hex = "#60CDFF"
        if self.manager.folders_data:
            _, _, accent_hex = get_tile_colors(self.manager.folders_data[0])

        if self.manager.edit_mode:
            pen = QPen(QColor("#F6AD55"), 2.0, Qt.PenStyle.DashLine)
            painter.setPen(pen)
        elif self.manager.temp_topmost_active:
            pen = QPen(QColor("#60CDFF"), 2.2)
            painter.setPen(pen)
        elif border_alpha > 0:
            b_col = QColor(accent_hex) if use_accent else QColor(self.manager.settings.get("dock_border_color", "#FFFFFF"))
            b_col.setAlpha(border_alpha)
            pen = QPen(b_col, 1.8 if use_accent else 1.2)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
        else:
            painter.setPen(Qt.PenStyle.NoPen)

        if self.manager.settings.get("dock_edge_fade", False):
            mode = self.manager.settings.get("layout_mode", "dock_horizontal")
            if mode == "dock_horizontal":
                grad = QLinearGradient(rect.left(), rect.center().y(), rect.right(), rect.center().y())
            else:
                grad = QLinearGradient(rect.center().x(), rect.top(), rect.center().x(), rect.bottom())

            fade_strength = self.manager.settings.get("dock_edge_fade_strength", 85) / 100.0
            edge_alpha = int(bg_alpha * (1.0 - fade_strength))

            c_edge = QColor(base_col.red(), base_col.green(), base_col.blue(), max(0, edge_alpha))
            c_mid = QColor(base_col.red(), base_col.green(), base_col.blue(), bg_alpha)

            grad.setColorAt(0.0, c_edge)
            grad.setColorAt(0.18, c_mid)
            grad.setColorAt(0.82, c_mid)
            grad.setColorAt(1.0, c_edge)
            painter.setBrush(grad)
        else:
            c_solid = QColor(base_col.red(), base_col.green(), base_col.blue(), bg_alpha)
            painter.setBrush(c_solid)

        path = self.build_dock_path(rect)
        painter.drawPath(path)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.manager.edit_mode:
            self.drag_start_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton and self.drag_start_pos and self.manager.edit_mode:
            diff = event.globalPosition().toPoint() - self.drag_start_pos
            self.move(self.pos() + diff)
            self.drag_start_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.drag_start_pos:
            if self.manager.settings.get("snap_to_grid", True):
                self.move(round(self.x() / 10) * 10, round(self.y() / 10) * 10)
            self.manager.settings["dock_x"] = self.x()
            self.manager.settings["dock_y"] = self.y()
            self.update_docked_edge()
            self.manager.save_config()
            self.drag_start_pos = None


class FolderManager:
    def __init__(self, app):
        global _CURRENT_LANG
        self.app = app
        self.dock_window = None
        self.standalone_widgets = []
        self.running_procs = set()
        self.active_popup = None
        self.settings_dialog = None
        self.about_dialog = None
        self.proc_worker = None
        self.warmer_worker = None
        self.edit_mode = False
        self.temp_topmost_active = False

        app_ic_path = find_app_icon_path()
        self.app_icon = QIcon(app_ic_path) if app_ic_path else self.app.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
        self.app.setWindowIcon(self.app_icon)

        self.app.aboutToQuit.connect(self.on_app_quit)

        self.settings = {
            "language": _CURRENT_LANG,
            "global_theme": "Тёмное стекло (Win 11)",
            "custom_global_themes": {},
            "layout_mode": "dock_horizontal",
            "apply_to_all": True,
            "show_dock_bg": True,
            "dock_shape": "rounded",
            "dock_slant": 24,
            "dock_corner_radius": 14,
            "dock_bg_color": "#12131A",
            "dock_bg_opacity": 175,
            "dock_edge_fade": False,
            "dock_edge_fade_strength": 85,
            "dock_border_color": "#FFFFFF",
            "dock_border_opacity": 65,
            "dock_accent_border": False,
            "dock_x": 260,
            "dock_y": 40,
            "snap_to_grid": True,
            "lock_position": False,
            "auto_hide": False,
            "open_on_hover": False,
            "hover_animation": True,
            "animation_style": "wave",
            "Summon_hotkey": "alt_space",
            "show_favorites_folder": False,
            "show_running_indicator": True,
            "always_on_top": False,
            "popup_bg_color": "#181922",
            "popup_bg_opacity": 242,
            "popup_display_mode": "multicolumn",
            "popup_items_per_col": 7,
            "popup_grid_cols": 4,
            "popup_width": 235,
            "popup_icon_size": 24,
            "popup_font_size": 13,
            "popup_padding": 7,
            "popup_max_height": 360
        }
        self.folders_data = []

        self.temp_topmost_watch_timer = QTimer()
        self.temp_topmost_watch_timer.setInterval(60)
        self.temp_topmost_watch_timer.timeout.connect(self.check_temp_topmost_outside_click)
        self._summon_grace_until = 0.0

        self.load_config()
        _CURRENT_LANG = self.settings.get("language", _CURRENT_LANG)
        self.setup_tray()
        self.sync_favorites_folder()
        self.rebuild_ui()

        self.hk_filter = HotkeyEventFilter(self.on_hotkey_pressed)
        self.app.installNativeEventFilter(self.hk_filter)
        self.register_global_hotkey()

        QTimer.singleShot(1200, self.start_background_warmer)
        QTimer.singleShot(800, self.trigger_async_process_scan)

        self.proc_timer = QTimer()
        self.proc_timer.timeout.connect(self.trigger_async_process_scan)
        self.proc_timer.start(6000)

    def start_background_warmer(self):
        if self.warmer_worker and self.warmer_worker.isRunning():
            return
        self.warmer_worker = BackgroundWarmerThread(self.folders_data)
        self.warmer_worker.finished_warming.connect(self.on_warmer_finished)
        self.warmer_worker.start(QThread.Priority.LowPriority)

    def on_warmer_finished(self, config_dirty: bool):
        if config_dirty:
            self.save_config()
        self.trigger_async_process_scan()

    def set_language(self, lang: str):
        global _CURRENT_LANG
        if lang not in ("ru", "en"):
            return
        _CURRENT_LANG = lang
        self.settings["language"] = lang
        save_language_to_registry(lang)
        self.save_config()
        self.update_tray_menu()
        self.refresh_appearance()

    def on_app_quit(self):
        try:
            user32.UnregisterHotKey(None, HOTKEY_ID)
        except Exception:
            pass
        self.save_config()

    def register_global_hotkey(self):
        try:
            user32.UnregisterHotKey(None, HOTKEY_ID)
        except Exception:
            pass

        hk_key = self.settings.get("Summon_hotkey", "alt_space")
        mods, vk, _ = HOTKEY_PRESETS.get(hk_key, (0, 0, ""))
        if vk != 0:
            user32.RegisterHotKey(None, HOTKEY_ID, mods | 0x4000, vk)

    def on_hotkey_pressed(self):
        if self.temp_topmost_active:
            self.deactivate_temp_topmost()
        else:
            self.activate_temp_topmost()

    def activate_temp_topmost(self):
        self.temp_topmost_active = True
        self._summon_grace_until = time.monotonic() + 0.35

        if self.dock_window:
            if self.dock_window.is_hidden_at_edge:
                self.dock_window.slide_to_visible()
            set_window_topmost_win32(self.dock_window, True)
            self.dock_window.showNormal()
            self.dock_window.raise_()
            self.dock_window.update()

        for w in self.standalone_widgets:
            set_window_topmost_win32(w, True)
            w.showNormal()
            w.raise_()
            w.update()

        self.temp_topmost_watch_timer.start()

    def deactivate_temp_topmost(self):
        if not self.temp_topmost_active:
            return
        self.temp_topmost_active = False
        self.temp_topmost_watch_timer.stop()

        if self.active_popup and self.active_popup.isVisible():
            self.active_popup.close()

        keep_top = self.settings.get("always_on_top", False) or self.settings.get("auto_hide", False)
        if self.dock_window:
            set_window_topmost_win32(self.dock_window, keep_top)
            if not keep_top:
                self.dock_window.lower()
            self.dock_window.update()

        for w in self.standalone_widgets:
            set_window_topmost_win32(w, keep_top)
            if not keep_top:
                w.lower()
            w.update()

    def check_temp_topmost_outside_click(self):
        if not self.temp_topmost_active:
            self.temp_topmost_watch_timer.stop()
            return
        if time.monotonic() < self._summon_grace_until:
            return
        if not is_any_mouse_button_down():
            return

        cpos = QCursor.pos()
        if self.dock_window and QRectF(self.dock_window.geometry()).contains(QPointF(cpos)):
            return
        for w in self.standalone_widgets:
            if QRectF(w.geometry()).contains(QPointF(cpos)):
                return
        if self.active_popup and self.active_popup.isVisible():
            if QRectF(self.active_popup.geometry()).contains(QPointF(cpos)):
                return

        self.deactivate_temp_topmost()

    def get_all_tiles(self):
        if self.dock_window:
            return self.dock_window.tiles
        return self.standalone_widgets

    def toggle_edit_mode(self, enabled: bool):
        self.edit_mode = enabled
        if self.active_popup and self.active_popup.isVisible():
            self.active_popup.close()
        if self.dock_window:
            if enabled:
                if not self.dock_window.wave_timer.isActive():
                    self.dock_window.wave_timer.start()
            else:
                self.dock_window.reset_wave_targets()
            self.dock_window.update()
        for w in self.standalone_widgets:
            w.update()
        if not enabled:
            self.save_config()
        self.update_tray_menu()

    def center_dock_panel(self):
        if self.dock_window:
            self.dock_window.center_on_screen()

    def sync_favorites_folder(self):
        want_fav = self.settings.get("show_favorites_folder", False)
        existing_fav = next((f for f in self.folders_data if f.get("is_favorites")), None)
        fav_img = "icons/Favorite.png" if resolve_image_path("icons/Favorite.png") else find_app_icon_path()

        if want_fav and not existing_fav:
            sample = self.folders_data[0] if self.folders_data else {}
            fav_folder = {
                "title": tr("def_fav_title"),
                "is_favorites": True,
                "x": 160,
                "y": 40,
                "size": sample.get("size", 88),
                "title_font_size": sample.get("title_font_size", 0),
                "theme": "Золотое Избранное",
                "image_path": fav_img,
                "show_title": sample.get("show_title", True),
                "icon_only": sample.get("icon_only", False),
                "show_badge": sample.get("show_badge", True),
                "apps": [
                    {"name": tr("def_downloads"), "path": os.path.expanduser("~\\Downloads"), "is_dir": True, "exe_name": ""},
                    {"name": tr("def_documents"), "path": os.path.expanduser("~\\Documents"), "is_dir": True, "exe_name": ""},
                ]
            }
            self.folders_data.append(fav_folder)
            self.save_config()
        elif not want_fav and existing_fav and len(self.folders_data) > 1:
            self.settings["saved_favorites_apps"] = existing_fav.get("apps", [])
            self.folders_data.remove(existing_fav)
            self.save_config()
        elif want_fav and existing_fav:
            if not existing_fav.get("image_path") and fav_img:
                existing_fav["image_path"] = fav_img
            if "saved_favorites_apps" in self.settings and not existing_fav.get("apps"):
                existing_fav["apps"] = self.settings.pop("saved_favorites_apps")

    def heal_and_prewarm_cache(self):
        clear_all_caches(clear_disk_cache=True)
        for folder in self.folders_data:
            for app_item in folder.get("apps", []):
                app_item.pop("exe_name", None)
        self.start_background_warmer()

    def trigger_async_process_scan(self):
        if not self.settings.get("show_running_indicator", True):
            return
        if self.proc_worker and self.proc_worker.isRunning():
            return
        self.proc_worker = ProcessMonitorThread()
        self.proc_worker.processes_updated.connect(self.on_processes_updated)
        self.proc_worker.start(QThread.Priority.LowPriority)

    def on_processes_updated(self, new_procs: set):
        if new_procs != self.running_procs:
            self.running_procs = new_procs
            if self.dock_window:
                for t in self.dock_window.tiles:
                    t.update()
            for w in self.standalone_widgets:
                w.update()

    def setup_tray(self):
        self.tray = QSystemTrayIcon(self.app)
        self.tray.setIcon(self.app_icon)
        self.tray.setToolTip(f"{APP_TITLE} v{APP_VERSION}")

        self.tray_menu = QMenu()
        self.update_tray_menu()
        self.tray.setContextMenu(self.tray_menu)
        self.tray.activated.connect(self.on_tray_click)
        self.tray.show()

    def update_tray_menu(self):
        pop_bg_hex = self.settings.get("popup_bg_color", "#181922")
        self.tray_menu.setStyleSheet(get_menu_stylesheet(pop_bg_hex))
        self.tray_menu.clear()

        show_act = self.tray_menu.addAction(get_menu_icon("up", pop_bg_hex), tr("tray_show_top"))
        center_act = self.tray_menu.addAction(get_menu_icon("center", pop_bg_hex), tr("ctx_center_dock"))
        edit_act = self.tray_menu.addAction(
            get_menu_icon("edit_move", pop_bg_hex),
            tr("edit_done") if self.edit_mode else tr("edit_start")
        )
        edit_act.setCheckable(True)
        edit_act.setChecked(self.edit_mode)

        rescan_act = self.tray_menu.addAction(get_menu_icon("rescan", pop_bg_hex), tr("ctx_rescan"))

        autostart_act = self.tray_menu.addAction(tr("tray_autostart"))
        autostart_act.setCheckable(True)
        autostart_act.setChecked(is_autostart_enabled())

        settings_act = self.tray_menu.addAction(get_menu_icon("settings", pop_bg_hex), tr("menu_settings"))
        about_act = self.tray_menu.addAction(get_menu_icon("about", pop_bg_hex), tr("menu_about"))
        self.tray_menu.addSeparator()
        quit_act = self.tray_menu.addAction(get_menu_icon("quit", pop_bg_hex), tr("menu_quit"))

        show_act.triggered.connect(self.activate_temp_topmost)
        center_act.triggered.connect(self.center_dock_panel)
        edit_act.triggered.connect(self.toggle_edit_mode)
        rescan_act.triggered.connect(self.force_reload_icons)
        autostart_act.triggered.connect(lambda checked: set_autostart(checked))
        settings_act.triggered.connect(lambda: self.open_settings_dialog(None))
        about_act.triggered.connect(self.open_about_dialog)
        quit_act.triggered.connect(self.app.quit)

    def toggle_favorites_folder(self, checked):
        self.settings["show_favorites_folder"] = checked
        self.sync_favorites_folder()
        self.rebuild_ui()
        self.update_tray_menu()

    def force_reload_icons(self):
        self.heal_and_prewarm_cache()
        self.refresh_appearance()

    def open_settings_dialog(self, tile=None, initial_tab=0):
        if self.settings_dialog and self.settings_dialog.isVisible():
            self.settings_dialog.close()
        self.settings_dialog = UnifiedSettingsDialog(self, tile, initial_tab=initial_tab)
        self.settings_dialog.show()
        self.settings_dialog.raise_()
        self.settings_dialog.activateWindow()

    def open_about_dialog(self):
        if self.about_dialog and self.about_dialog.isVisible():
            self.about_dialog.close()
        self.about_dialog = AboutDialog(self)
        self.about_dialog.show()
        self.about_dialog.raise_()
        self.about_dialog.activateWindow()

    def toggle_auto_hide(self, checked):
        self.settings["auto_hide"] = checked
        self.save_config()
        self.rebuild_ui()
        self.update_tray_menu()

    def on_tray_click(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.activate_temp_topmost()

    def load_config(self):
        global _CURRENT_LANG
        installer_lang = get_installer_language_from_registry()
        candidates = [CONFIG_FILE, os.path.join(BASE_DIR, "folders_config.json")]
        loaded = False
        for cfg_p in candidates:
            if os.path.exists(cfg_p):
                try:
                    with open(cfg_p, "r", encoding="utf-8") as f:
                        raw = json.load(f)
                    if isinstance(raw, list):
                        self.folders_data = raw
                    elif isinstance(raw, dict):
                        self.settings.update(raw.get("settings", {}))
                        self.folders_data = raw.get("folders", [])
                    loaded = True
                    break
                except Exception:
                    pass

        if installer_lang in ("ru", "en") and not loaded:
            self.settings["language"] = installer_lang
        _CURRENT_LANG = self.settings.get("language", installer_lang)

        if not loaded or not self.folders_data:
            self.folders_data = [
                {
                    "title": f"{tr('def_shortcut')} 1", "x": 280, "y": 40, "size": 88, "title_font_size": 0,
                    "theme": "Тёмное стекло (Win 11)", "image_path": "",
                    "show_title": True, "icon_only": False, "show_badge": True,
                    "apps": [
                        {"name": tr("def_notepad"), "path": "C:\\Windows\\System32\\notepad.exe", "exe_name": "notepad.exe"},
                        {"name": tr("def_calc"), "path": "C:\\Windows\\System32\\calc.exe", "exe_name": "calc.exe"}
                    ]
                },
                {
                    "title": f"{tr('def_shortcut')} 2", "x": 388, "y": 40, "size": 88, "title_font_size": 0,
                    "theme": "Тёмное стекло (Win 11)", "image_path": "",
                    "show_title": True, "icon_only": False, "show_badge": True,
                    "apps": []
                },
                {
                    "title": f"{tr('def_shortcut')} 3", "x": 496, "y": 40, "size": 88, "title_font_size": 0,
                    "theme": "Тёмное стекло (Win 11)", "image_path": "",
                    "show_title": True, "icon_only": False, "show_badge": True,
                    "apps": []
                }
            ]
            self.save_config()

    def save_config(self):
        global CONFIG_FILE
        clean_folders = []
        for f in self.folders_data:
            f_copy = dict(f)
            clean_apps = []
            for a in f.get("apps", []):
                clean_apps.append({k: v for k, v in a.items() if not k.startswith("_")})
            f_copy["apps"] = clean_apps
            clean_folders.append(f_copy)

        payload = {
            "settings": self.settings,
            "folders": clean_folders
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=4)
                f.flush()
                os.fsync(f.fileno())
        except Exception:
            try:
                os.makedirs(APPDATA_DIR, exist_ok=True)
                CONFIG_FILE = os.path.join(APPDATA_DIR, "folders_config.json")
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(payload, f, ensure_ascii=False, indent=4)
                    f.flush()
                    os.fsync(f.fileno())
            except Exception as e:
                print(f"Save error: {e}")

    def rebuild_ui(self):
        if self.dock_window:
            self.dock_window.close()
            self.dock_window = None
        for w in self.standalone_widgets:
            w.close()
        self.standalone_widgets.clear()

        mode = self.settings.get("layout_mode", "dock_horizontal")
        if mode in ("dock_horizontal", "dock_vertical"):
            self.dock_window = DockPanelWindow(self)
        else:
            for f_data in self.folders_data:
                w = FolderTile(self, f_data, parent=None, is_standalone=True)
                self.standalone_widgets.append(w)

    def refresh_appearance(self):
        if self.dock_window:
            for t in self.dock_window.tiles:
                t.update_appearance()
            self.dock_window.update_margins_and_repaint()
        for w in self.standalone_widgets:
            w.update_appearance()
        self.update_tray_menu()

    def set_layout_mode(self, new_mode):
        self.settings["layout_mode"] = new_mode
        self.save_config()
        self.rebuild_ui()

    def create_new_folder(self, ref_tile=None):
        sample = self.folders_data[-1] if self.folders_data else {}
        new_data = {
            "title": f"{tr('def_shortcut')} {len(self.folders_data) + 1}",
            "x": (ref_tile.x() + ref_tile.width() + 15) if (ref_tile and ref_tile.is_standalone) else 200,
            "y": ref_tile.y() if (ref_tile and ref_tile.is_standalone) else 200,
            "size": sample.get("size", 88),
            "title_font_size": sample.get("title_font_size", 0),
            "theme": sample.get("theme", "Тёмное стекло (Win 11)"),
            "custom_bg_color": sample.get("custom_bg_color", ""),
            "custom_accent_color": sample.get("custom_accent_color", ""),
            "image_path": "",
            "show_title": sample.get("show_title", True),
            "icon_only": sample.get("icon_only", False),
            "show_badge": sample.get("show_badge", True),
            "apps": []
        }
        self.folders_data.append(new_data)
        self.save_config()
        if self.dock_window:
            self.dock_window.rebuild_panel()
        else:
            w = FolderTile(self, new_data, parent=None, is_standalone=True)
            self.standalone_widgets.append(w)

    def delete_folder(self, tile):
        if len(self.folders_data) <= 1:
            return
        if tile.data.get("is_favorites"):
            self.settings["show_favorites_folder"] = False
        self.folders_data.remove(tile.data)
        self.save_config()
        if self.dock_window:
            self.dock_window.rebuild_panel()
        else:
            self.standalone_widgets.remove(tile)
            tile.close()

    def show_context_menu(self, tile, global_pos):
        pop_bg_hex = self.settings.get("popup_bg_color", "#181922")
        _, _, acc_hex = get_tile_colors(tile.data)

        menu = QMenu()
        menu.setStyleSheet(get_menu_stylesheet(pop_bg_hex, acc_hex))

        pick_icon_act = menu.addAction(get_menu_icon("icon_pic", pop_bg_hex), tr("ctx_pick_folder_ic"))
        add_app_act = menu.addAction(get_menu_icon("add_app", pop_bg_hex), tr("ctx_add_app"))
        add_dir_act = menu.addAction(get_menu_icon("add_folder", pop_bg_hex), tr("ctx_add_dir"))
        add_web_act = menu.addAction(get_menu_icon("web", pop_bg_hex), tr("ctx_add_web"))
        rename_folder_act = menu.addAction(get_menu_icon("rename", pop_bg_hex), tr("ctx_rename_folder"))

        menu.addSeparator()
        new_folder_act = menu.addAction(get_menu_icon("add_app", pop_bg_hex), tr("ctx_new_folder"))
        delete_folder_act = menu.addAction(get_menu_icon("delete", pop_bg_hex), tr("ctx_del_folder"))

        menu.addSeparator()
        edit_label = tr("edit_done") if self.edit_mode else tr("edit_start")
        edit_panel_act = menu.addAction(get_menu_icon("edit_move", pop_bg_hex), edit_label)
        edit_panel_act.setCheckable(True)
        edit_panel_act.setChecked(self.edit_mode)

        center_dock_act = None
        if self.dock_window:
            center_dock_act = menu.addAction(get_menu_icon("center", pop_bg_hex), tr("ctx_center_dock"))

        rescan_act = menu.addAction(get_menu_icon("rescan", pop_bg_hex), tr("ctx_rescan"))

        menu.addSeparator()
        settings_act = menu.addAction(get_menu_icon("settings", pop_bg_hex), tr("menu_settings"))
        about_act = menu.addAction(get_menu_icon("about", pop_bg_hex), tr("menu_about"))

        menu.addSeparator()
        quit_act = menu.addAction(get_menu_icon("quit", pop_bg_hex), tr("menu_close_app"))

        action = menu.exec(global_pos)
        if not action:
            return

        if action == pick_icon_act:
            dlg = IconPickerDialog()
            if dlg.exec() == QDialog.DialogCode.Accepted and dlg.selected_icon:
                tile.data["image_path"] = dlg.selected_icon
                tile.update_appearance()
                self.save_config()
        elif action == add_app_act:
            tile.add_application()
        elif action == add_dir_act:
            tile.add_folder_link()
        elif action == add_web_act:
            tile.add_web_link()
        elif action == rename_folder_act:
            new_title, ok = QInputDialog.getText(
                None, tr("ctx_rename_folder"), tr("dlg_folder_name_l"), text=tile.data.get("title", tr("def_shortcut"))
            )
            if ok and new_title:
                tile.data["title"] = new_title
                tile.update_appearance()
                self.save_config()
        elif action == new_folder_act:
            self.create_new_folder(tile)
        elif action == delete_folder_act:
            self.delete_folder(tile)
        elif action == edit_panel_act:
            self.toggle_edit_mode(edit_panel_act.isChecked())
        elif center_dock_act and action == center_dock_act:
            self.center_dock_panel()
        elif action == rescan_act:
            self.force_reload_icons()
        elif action == settings_act:
            self.open_settings_dialog(tile)
        elif action == about_act:
            self.open_about_dialog()
        elif action == quit_act:
            self.app.quit()


if __name__ == "__main__":
    try:
        ole32.CoInitialize(None)
    except Exception:
        pass
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    manager = FolderManager(app)
    sys.exit(app.exec())