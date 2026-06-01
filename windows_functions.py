"""
FunctionWin - Streamlit Web App
Provides a web interface to interact with all Windows functions locally using natural language
Took idea from FunctionMac and created for Windows by Dhyey
"""

import json
import subprocess
import os
import ctypes
import ctypes.wintypes
import winreg
import psutil
import requests
from datetime import datetime
from typing import Optional, List, Dict, Any
import pyautogui
import time
import math
import numpy as np


# ============== Helper Functions ==============

def run_powershell(script: str, timeout: int = 30) -> str:
    """Execute a PowerShell script and return the result."""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if result.returncode != 0 and result.stderr:
            return f"Error: {result.stderr.strip()}"
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "Error: Command timed out"
    except Exception as e:
        return f"Error: {str(e)}"


def run_shell_command(command: str) -> str:
    """Execute a shell command and return the result."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0 and result.stderr:
            return f"Error: {result.stderr.strip()}"
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "Error: Command timed out"
    except Exception as e:
        return f"Error: {str(e)}"


# ============== Screenshot ==============

def _get_desktop_path() -> str:
    """Get real Desktop path, handles OneDrive redirection."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders")
        desktop, _ = winreg.QueryValueEx(key, "Desktop")
        winreg.CloseKey(key)
        return desktop
    except Exception:
        return os.path.expanduser("~\\Desktop")


def take_screenshot(save_path: str = "") -> str:
    """Take a screenshot and save it to the specified path."""
    try:
        if not save_path:
            expanded_path = os.path.join(_get_desktop_path(), "screenshot.png")
        else:
            expanded_path = os.path.expanduser(save_path)
        os.makedirs(os.path.dirname(os.path.abspath(expanded_path)), exist_ok=True)
        screenshot = pyautogui.screenshot()
        screenshot.save(expanded_path)
        return json.dumps({'success': True, 'path': expanded_path, 'message': f'Screenshot saved to {expanded_path}'})
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Failed to take screenshot: {str(e)}'})


# ============== Clipboard ==============

def copy_to_clipboard(text: str) -> str:
    """Copy text to clipboard."""
    try:
        script = f'Set-Clipboard -Value {json.dumps(text)}'
        result = run_powershell(script)
        if "Error" in result:
            return json.dumps({'success': False, 'error': f'Failed to copy to clipboard: {result}'})
        return json.dumps({'success': True, 'message': f'Copied "{text}" to clipboard'})
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Failed to copy to clipboard: {str(e)}'})


def get_clipboard_content() -> str:
    """Get current clipboard content."""
    try:
        content = run_powershell("Get-Clipboard")
        return json.dumps({'success': True, 'content': content})
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Failed to get clipboard content: {str(e)}'})


def paste_from_clipboard() -> str:
    """Get the current content from the system clipboard."""
    try:
        content = run_powershell("Get-Clipboard")
        if content:
            return json.dumps({'success': True, 'content': content, 'message': f'Clipboard content: {content}'})
        return json.dumps({'success': True, 'content': '', 'message': 'Clipboard is empty'})
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Error reading clipboard: {str(e)}'})


# ============== Theme ==============

def change_theme(theme: str) -> str:
    """
    Change Windows appearance theme (dark/light).

    Args:
        theme: "dark", "light", or "toggle"
    """
    try:
        theme = theme.lower().strip()
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"

        if theme == "dark":
            value = 0
        elif theme == "light":
            value = 1
        elif theme in ("toggle", "auto"):
            # Read current value and flip
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as k:
                current, _ = winreg.QueryValueEx(k, "AppsUseLightTheme")
            value = 1 - current
        else:
            return json.dumps({'success': False, 'error': f'Invalid theme: {theme}. Use "dark", "light", or "toggle"'})

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as k:
            winreg.SetValueEx(k, "AppsUseLightTheme", 0, winreg.REG_DWORD, value)
            winreg.SetValueEx(k, "SystemUsesLightTheme", 0, winreg.REG_DWORD, value)

        label = "light" if value == 1 else "dark"
        # Notify Windows to refresh
        run_powershell(
            "Add-Type -Name W -Namespace Win32 -MemberDefinition '[DllImport(\"user32.dll\")]public static extern IntPtr SendMessageTimeout(IntPtr hWnd,uint Msg,UIntPtr wParam,string lParam,uint fuFlags,uint uTimeout,out UIntPtr lpdwResult);'; "
            "$r=[UIntPtr]::Zero; [Win32.W]::SendMessageTimeout([IntPtr]0xFFFF,0x1a,[UIntPtr]::Zero,'ImmersiveColorSet',0,1000,[ref]$r)"
        )
        return json.dumps({'success': True, 'message': f'Successfully changed theme to: {label}'})
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Error changing theme: {str(e)}'})


def get_current_theme() -> str:
    """Get the current Windows appearance theme."""
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as k:
            value, _ = winreg.QueryValueEx(k, "AppsUseLightTheme")
        theme = "light" if value == 1 else "dark"
        return json.dumps({'success': True, 'theme': theme, 'message': f'Current theme: {theme}'})
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Error getting theme: {str(e)}'})


# ============== Volume ==============

def set_volume(level: int) -> str:
    """Set system volume level (0-100)."""
    try:
        if not 0 <= level <= 100:
            return json.dumps({'success': False, 'error': 'Volume level must be between 0 and 100'})
        ps_script = f"""
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
[ComImport, Guid("5CDF2C82-841E-4546-9722-0CF74078229A"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioEndpointVolume {{
    int r1(); int r2(); int r3(); int r4();
    int SetMasterVolumeLevelScalar(float fLevel, Guid pguidEventContext);
    int r6();
    int GetMasterVolumeLevelScalar(out float pfLevel);
    int r8(); int r9(); int r10(); int r11();
    int SetMute([MarshalAs(UnmanagedType.Bool)] bool bMute, Guid pguidEventContext);
    int GetMute([MarshalAs(UnmanagedType.Bool)] out bool pbMute);
}}
[ComImport, Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDeviceEnumerator {{
    int r1();
    int GetDefaultAudioEndpoint(int dataFlow, int role, out IMMDevice ppDevice);
}}
[ComImport, Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDevice {{
    int Activate(Guid iid, int dwClsCtx, IntPtr pActivationParams, [MarshalAs(UnmanagedType.IUnknown)] out object ppInterface);
}}
public class Vol {{
    static readonly Guid CLSID_MMDevEnum = new Guid("BCDE0395-E52F-467C-8E3D-C4579291692E");
    public static void Set(float v) {{
        var e = (IMMDeviceEnumerator)Activator.CreateInstance(Type.GetTypeFromCLSID(CLSID_MMDevEnum));
        IMMDevice d; e.GetDefaultAudioEndpoint(0, 0, out d);
        object a; d.Activate(typeof(IAudioEndpointVolume).GUID, 23, IntPtr.Zero, out a);
        ((IAudioEndpointVolume)a).SetMasterVolumeLevelScalar(v, Guid.Empty);
    }}
}}
'@
[Vol]::Set([float]({level / 100.0}))
"""
        result = run_powershell(ps_script)
        if "Error" in result:
            return json.dumps({'success': False, 'error': result})
        return json.dumps({'success': True, 'message': f'Volume set to {level}%', 'level': level})
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Failed to set volume: {str(e)}'})


def get_volume() -> str:
    """Get current system volume level."""
    try:
        ps_script = """
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
[ComImport, Guid("5CDF2C82-841E-4546-9722-0CF74078229A"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioEndpointVolume {
    int r1(); int r2(); int r3(); int r4();
    int SetMasterVolumeLevelScalar(float fLevel, Guid pguidEventContext);
    int r6();
    int GetMasterVolumeLevelScalar(out float pfLevel);
    int r8(); int r9(); int r10(); int r11();
    int SetMute([MarshalAs(UnmanagedType.Bool)] bool bMute, Guid pguidEventContext);
    int GetMute([MarshalAs(UnmanagedType.Bool)] out bool pbMute);
}
[ComImport, Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDeviceEnumerator {
    int r1();
    int GetDefaultAudioEndpoint(int dataFlow, int role, out IMMDevice ppDevice);
}
[ComImport, Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDevice {
    int Activate(Guid iid, int dwClsCtx, IntPtr pActivationParams, [MarshalAs(UnmanagedType.IUnknown)] out object ppInterface);
}
public class VolGet {
    static readonly Guid CLSID_MMDevEnum = new Guid("BCDE0395-E52F-467C-8E3D-C4579291692E");
    public static float Get() {
        var e = (IMMDeviceEnumerator)Activator.CreateInstance(Type.GetTypeFromCLSID(CLSID_MMDevEnum));
        IMMDevice d; e.GetDefaultAudioEndpoint(0, 0, out d);
        object a; d.Activate(typeof(IAudioEndpointVolume).GUID, 23, IntPtr.Zero, out a);
        float v; ((IAudioEndpointVolume)a).GetMasterVolumeLevelScalar(out v);
        return v;
    }
}
'@
[math]::Round([VolGet]::Get()*100)
"""
        result = run_powershell(ps_script)
        if result.lstrip('-').isdigit() or result.replace('.', '', 1).isdigit():
            level = int(float(result))
            return json.dumps({'success': True, 'volume': level, 'message': f'Current volume: {level}%'})
        return json.dumps({'success': False, 'error': f'Could not read volume: {result}'})
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Failed to get volume: {str(e)}'})


def mute_volume() -> str:
    """Mute system volume."""
    try:
        ps_script = """
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
[ComImport, Guid("5CDF2C82-841E-4546-9722-0CF74078229A"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioEndpointVolume {
    int r1(); int r2(); int r3(); int r4();
    int SetMasterVolumeLevelScalar(float fLevel, Guid pguidEventContext);
    int r6();
    int GetMasterVolumeLevelScalar(out float pfLevel);
    int r8(); int r9(); int r10(); int r11();
    int SetMute([MarshalAs(UnmanagedType.Bool)] bool bMute, Guid pguidEventContext);
    int GetMute([MarshalAs(UnmanagedType.Bool)] out bool pbMute);
}
[ComImport, Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDeviceEnumerator {
    int r1();
    int GetDefaultAudioEndpoint(int dataFlow, int role, out IMMDevice ppDevice);
}
[ComImport, Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDevice {
    int Activate(Guid iid, int dwClsCtx, IntPtr pActivationParams, [MarshalAs(UnmanagedType.IUnknown)] out object ppInterface);
}
public class VolMute {
    static readonly Guid CLSID_MMDevEnum = new Guid("BCDE0395-E52F-467C-8E3D-C4579291692E");
    public static void Mute() {
        var e = (IMMDeviceEnumerator)Activator.CreateInstance(Type.GetTypeFromCLSID(CLSID_MMDevEnum));
        IMMDevice d; e.GetDefaultAudioEndpoint(0, 0, out d);
        object a; d.Activate(typeof(IAudioEndpointVolume).GUID, 23, IntPtr.Zero, out a);
        ((IAudioEndpointVolume)a).SetMute(true, Guid.Empty);
    }
}
'@
[VolMute]::Mute()
"""
        result = run_powershell(ps_script)
        if "Error" in result:
            return json.dumps({'success': False, 'error': result})
        return json.dumps({'success': True, 'message': 'Volume muted'})
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Failed to mute: {str(e)}'})


def unmute_volume() -> str:
    """Unmute system volume."""
    try:
        ps_script = """
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
[ComImport, Guid("5CDF2C82-841E-4546-9722-0CF74078229A"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioEndpointVolume {
    int r1(); int r2(); int r3(); int r4();
    int SetMasterVolumeLevelScalar(float fLevel, Guid pguidEventContext);
    int r6();
    int GetMasterVolumeLevelScalar(out float pfLevel);
    int r8(); int r9(); int r10(); int r11();
    int SetMute([MarshalAs(UnmanagedType.Bool)] bool bMute, Guid pguidEventContext);
    int GetMute([MarshalAs(UnmanagedType.Bool)] out bool pbMute);
}
[ComImport, Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDeviceEnumerator {
    int r1();
    int GetDefaultAudioEndpoint(int dataFlow, int role, out IMMDevice ppDevice);
}
[ComImport, Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDevice {
    int Activate(Guid iid, int dwClsCtx, IntPtr pActivationParams, [MarshalAs(UnmanagedType.IUnknown)] out object ppInterface);
}
public class VolUnmute {
    static readonly Guid CLSID_MMDevEnum = new Guid("BCDE0395-E52F-467C-8E3D-C4579291692E");
    public static void Unmute() {
        var e = (IMMDeviceEnumerator)Activator.CreateInstance(Type.GetTypeFromCLSID(CLSID_MMDevEnum));
        IMMDevice d; e.GetDefaultAudioEndpoint(0, 0, out d);
        object a; d.Activate(typeof(IAudioEndpointVolume).GUID, 23, IntPtr.Zero, out a);
        ((IAudioEndpointVolume)a).SetMute(false, Guid.Empty);
    }
}
'@
[VolUnmute]::Unmute()
"""
        result = run_powershell(ps_script)
        if "Error" in result:
            return json.dumps({'success': False, 'error': result})
        return json.dumps({'success': True, 'message': 'Volume unmuted'})
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Failed to unmute: {str(e)}'})


# ============== Brightness ==============

def set_brightness(level: int) -> str:
    """Set screen brightness level (0-100). Works on laptops with WMI support."""
    try:
        if not 0 <= level <= 100:
            return json.dumps({'success': False, 'error': 'Brightness level must be between 0 and 100'})

        # Approach 1: WMI (works on most laptops)
        ps_script = f"""
(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, {level})
"""
        result = run_powershell(ps_script)
        if "Error" not in result and "Exception" not in result:
            return json.dumps({'success': True, 'message': f'Brightness set to {level}%', 'level': level})

        # Approach 2: nircmd (if installed)
        result2 = run_shell_command(f'nircmd changebrightness {level}')
        if "Error" not in result2:
            return json.dumps({'success': True, 'message': f'Brightness set to {level}% via nircmd', 'level': level})

        return json.dumps({
            'success': False,
            'error': 'Could not set brightness. Note: WMI brightness control only works on laptops. For desktops, use your monitor\'s physical buttons or install nircmd.'
        })
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Failed to set brightness: {str(e)}'})


def get_brightness() -> str:
    """Get the current screen brightness level."""
    try:
        ps_script = "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness"
        result = run_powershell(ps_script)
        if result.strip().isdigit():
            level = int(result.strip())
            return json.dumps({'success': True, 'brightness': level, 'message': f'Current brightness: {level}%'})
        return json.dumps({'success': False, 'error': 'Could not retrieve brightness (WMI unavailable or desktop monitor)'})
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Error getting brightness: {str(e)}'})


# ============== Focus / Do Not Disturb ==============

def enable_do_not_disturb() -> str:
    """Enable Focus Assist (Do Not Disturb) on Windows."""
    try:
        # Windows 10/11: Focus Assist via registry
        key_path = r"Software\Microsoft\Windows\CurrentVersion\CloudStore\Store\DefaultAccount\Current\default$windows.data.notifications.quiethourssettings\windows.data.notifications.quiethourssettings"
        try:
            # Toggle Focus Assist ON via registry (value: 1 = priority, 2 = alarms only)
            ps_script = r"""
$registryPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Notifications\Settings"
Set-ItemProperty -Path $registryPath -Name "NOC_GLOBAL_SETTING_TOASTS_ENABLED" -Value 0 -Type DWord -Force 2>$null
Write-Output "success"
"""
            result = run_powershell(ps_script)
            if "success" in result:
                return json.dumps({'success': True, 'message': 'Focus Assist (Do Not Disturb) enabled - notifications suppressed'})
        except Exception:
            pass

        return json.dumps({'success': True, 'message': 'Focus Assist setting updated. You may need to toggle it from Action Center for full effect.'})
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Error enabling Focus Assist: {str(e)}'})


def disable_do_not_disturb() -> str:
    """Disable Focus Assist (Do Not Disturb) on Windows."""
    try:
        ps_script = r"""
$registryPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Notifications\Settings"
Set-ItemProperty -Path $registryPath -Name "NOC_GLOBAL_SETTING_TOASTS_ENABLED" -Value 1 -Type DWord -Force 2>$null
Write-Output "success"
"""
        result = run_powershell(ps_script)
        if "success" in result:
            return json.dumps({'success': True, 'message': 'Focus Assist disabled - notifications re-enabled'})
        return json.dumps({'success': False, 'error': 'Could not disable Focus Assist'})
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Error disabling Focus Assist: {str(e)}'})


# ============== File Operations ==============

def find_files(folder_path: str, file_name: str = "", file_extension: str = "") -> str:
    """Find files in a specific folder by name or extension."""
    try:
        expanded_path = os.path.expanduser(folder_path)
        if not os.path.exists(expanded_path):
            return json.dumps({'success': False, 'error': f'Folder does not exist: {expanded_path}'})

        found_files = []
        for root, dirs, files in os.walk(expanded_path):
            for file in files:
                full_path = os.path.join(root, file)
                if file_name and file_name.lower() not in file.lower():
                    continue
                if file_extension:
                    ext = file_extension.lower() if file_extension.startswith('.') else '.' + file_extension.lower()
                    if not file.lower().endswith(ext):
                        continue
                try:
                    stat = os.stat(full_path)
                    found_files.append({
                        'name': file,
                        'path': full_path,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    })
                except Exception:
                    found_files.append({'name': file, 'path': full_path})

        return json.dumps({
            'success': True,
            'count': len(found_files),
            'files': found_files[:50],
            'message': f'Found {len(found_files)} files'
        })
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Error finding files: {str(e)}'})


def open_file(file_path: str) -> str:
    """Open a file with its default application."""
    try:
        expanded_path = os.path.expanduser(file_path)
        if not os.path.exists(expanded_path):
            return json.dumps({'success': False, 'error': f'File not found: {expanded_path}'})
        os.startfile(expanded_path)
        return json.dumps({'success': True, 'message': f'Opened file: {expanded_path}'})
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Failed to open file: {str(e)}'})


def open_folder(folder_path: str) -> str:
    """Open a folder in Windows Explorer."""
    try:
        expanded_path = os.path.expanduser(folder_path)
        if not os.path.exists(expanded_path):
            return json.dumps({'success': False, 'error': f'Folder not found: {expanded_path}'})
        subprocess.Popen(['explorer', expanded_path])
        return json.dumps({'success': True, 'message': f'Opened folder: {expanded_path}'})
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Failed to open folder: {str(e)}'})


# ============== System Info ==============

def get_battery_info() -> str:
    """Get battery information."""
    try:
        battery = psutil.sensors_battery()
        if battery is None:
            return json.dumps({'success': False, 'error': 'No battery detected (desktop PC)'})
        status = "Charging" if battery.power_plugged else "Discharging"
        secs_left = battery.secsleft
        time_left = "Calculating..." if secs_left == psutil.POWER_TIME_UNKNOWN else \
                    f"{secs_left // 3600}h {(secs_left % 3600) // 60}m" if secs_left != psutil.POWER_TIME_UNLIMITED else "Plugged in"
        return json.dumps({
            'success': True,
            'percentage': round(battery.percent, 1),
            'status': status,
            'plugged_in': battery.power_plugged,
            'time_remaining': time_left,
            'message': f'Battery: {battery.percent:.1f}% ({status})'
        })
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Failed to get battery info: {str(e)}'})


def get_system_info() -> str:
    """Get comprehensive system information."""
    try:
        import platform
        uname = platform.uname()
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime_secs = (datetime.now() - boot_time).total_seconds()
        uptime_str = f"{int(uptime_secs // 3600)}h {int((uptime_secs % 3600) // 60)}m"

        ps_script = "(Get-WmiObject Win32_ComputerSystem).TotalPhysicalMemory"
        total_ram_str = run_powershell(ps_script)
        total_ram = int(total_ram_str.strip()) // (1024 ** 3) if total_ram_str.strip().isdigit() else "N/A"

        info = {
            'success': True,
            'hostname': uname.node,
            'os': f"{uname.system} {uname.release}",
            'os_version': uname.version,
            'architecture': uname.machine,
            'processor': uname.processor,
            'total_ram_gb': total_ram,
            'uptime': uptime_str,
            'boot_time': boot_time.strftime('%Y-%m-%d %H:%M:%S'),
            'python_version': platform.python_version()
        }
        return json.dumps(info)
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Failed to get system info: {str(e)}'})


def get_cpu_usage() -> str:
    """Get current CPU usage."""
    try:
        usage = psutil.cpu_percent(interval=1)
        count = psutil.cpu_count(logical=True)
        physical = psutil.cpu_count(logical=False)
        freq = psutil.cpu_freq()
        return json.dumps({
            'success': True,
            'usage_percent': usage,
            'logical_cores': count,
            'physical_cores': physical,
            'frequency_mhz': round(freq.current, 1) if freq else 'N/A',
            'message': f'CPU usage: {usage}%'
        })
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Failed to get CPU usage: {str(e)}'})


def get_memory_usage() -> str:
    """Get current memory usage."""
    try:
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        return json.dumps({
            'success': True,
            'total_gb': round(mem.total / (1024 ** 3), 2),
            'used_gb': round(mem.used / (1024 ** 3), 2),
            'available_gb': round(mem.available / (1024 ** 3), 2),
            'percent_used': mem.percent,
            'swap_total_gb': round(swap.total / (1024 ** 3), 2),
            'swap_used_gb': round(swap.used / (1024 ** 3), 2),
            'message': f'Memory: {mem.percent}% used ({round(mem.used/(1024**3),1)}GB / {round(mem.total/(1024**3),1)}GB)'
        })
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Failed to get memory usage: {str(e)}'})


def get_disk_usage() -> str:
    """Get disk usage information for all drives."""
    try:
        disks = []
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disks.append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'filesystem': partition.fstype,
                    'total_gb': round(usage.total / (1024 ** 3), 2),
                    'used_gb': round(usage.used / (1024 ** 3), 2),
                    'free_gb': round(usage.free / (1024 ** 3), 2),
                    'percent_used': usage.percent
                })
            except PermissionError:
                pass
        return json.dumps({'success': True, 'disks': disks, 'message': f'Found {len(disks)} disk(s)'})
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Failed to get disk usage: {str(e)}'})


# ============== Application Control ==============

def open_application(app_name: str) -> str:
    """Open a Windows application by name."""
    try:
        # Try direct start command (works for many Windows apps)
        result = subprocess.Popen(
            ['start', '', app_name],
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(0.5)
        return json.dumps({'success': True, 'message': f'Launched: {app_name}'})
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Failed to open {app_name}: {str(e)}'})


def quit_application(app_name: str) -> str:
    """Quit a running application by process name."""
    try:
        killed = []
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                if app_name.lower() in proc.info['name'].lower():
                    proc.terminate()
                    killed.append(proc.info['name'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        if killed:
            return json.dumps({'success': True, 'message': f'Terminated: {", ".join(killed)}'})
        return json.dumps({'success': False, 'error': f'No running process found matching: {app_name}'})
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Failed to quit {app_name}: {str(e)}'})


def list_running_applications() -> str:
    """List all currently running applications (visible windows only)."""
    try:
        ps_script = """
Get-Process | Where-Object {$_.MainWindowTitle -ne ""} | Select-Object Name, Id, CPU, WorkingSet | ConvertTo-Json
"""
        result = run_powershell(ps_script)
        try:
            apps = json.loads(result)
            if isinstance(apps, dict):
                apps = [apps]
            formatted = [
                {
                    'name': a.get('Name', ''),
                    'pid': a.get('Id', ''),
                    'cpu': round(a.get('CPU', 0) or 0, 1),
                    'memory_mb': round((a.get('WorkingSet', 0) or 0) / (1024 * 1024), 1)
                }
                for a in apps
            ]
            return json.dumps({'success': True, 'count': len(formatted), 'applications': formatted})
        except Exception:
            return json.dumps({'success': False, 'error': f'Could not parse process list: {result[:200]}'})
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Failed to list applications: {str(e)}'})


# ============== Mouse & Keyboard ==============

def click_at_coordinates(x: int, y: int) -> str:
    """Click the mouse at specific screen coordinates."""
    try:
        pyautogui.click(x, y)
        return json.dumps({'success': True, 'message': f'Clicked at ({x}, {y})'})
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Failed to click: {str(e)}'})


def drag_mouse(start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 1.0) -> str:
    """Drag the mouse from one position to another."""
    try:
        pyautogui.moveTo(start_x, start_y)
        pyautogui.dragTo(end_x, end_y, duration=duration, button='left')
        return json.dumps({'success': True, 'message': f'Dragged from ({start_x},{start_y}) to ({end_x},{end_y})'})
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Failed to drag mouse: {str(e)}'})


def type_text(text: str, interval: float = 0.05) -> str:
    """Type text using the keyboard."""
    try:
        pyautogui.typewrite(text, interval=interval)
        return json.dumps({'success': True, 'message': f'Typed: "{text}"'})
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Failed to type text: {str(e)}'})


def send_keyboard_shortcut(keys: str) -> str:
    """
    Send a keyboard shortcut.
    Examples: 'ctrl+c', 'ctrl+alt+del', 'win+d', 'alt+f4'
    """
    try:
        pyautogui.hotkey(*keys.lower().replace('+', ' ').split())
        return json.dumps({'success': True, 'message': f'Sent shortcut: {keys}'})
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Failed to send shortcut: {str(e)}'})


def scroll_screen(direction: str, clicks: int = 3, x: Optional[int] = None, y: Optional[int] = None) -> str:
    """Scroll the screen in a direction."""
    try:
        if x is not None and y is not None:
            pyautogui.moveTo(x, y)
        amount = clicks if direction.lower() == 'up' else -clicks
        pyautogui.scroll(amount)
        return json.dumps({'success': True, 'message': f'Scrolled {direction} {clicks} clicks'})
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Failed to scroll: {str(e)}'})


def get_mouse_position() -> str:
    """Get the current mouse cursor position."""
    try:
        pos = pyautogui.position()
        return json.dumps({'success': True, 'x': pos.x, 'y': pos.y, 'message': f'Mouse at ({pos.x}, {pos.y})'})
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Failed to get mouse position: {str(e)}'})


def get_screen_info() -> str:
    """Get screen resolution and display information."""
    try:
        width, height = pyautogui.size()
        ps_script = "Get-WmiObject Win32_VideoController | Select-Object Name,CurrentHorizontalResolution,CurrentVerticalResolution,AdapterRAM | ConvertTo-Json"
        result = run_powershell(ps_script)
        displays = []
        try:
            data = json.loads(result)
            if isinstance(data, dict):
                data = [data]
            for d in data:
                displays.append({
                    'name': d.get('Name', 'Unknown'),
                    'width': d.get('CurrentHorizontalResolution'),
                    'height': d.get('CurrentVerticalResolution'),
                    'vram_mb': round((d.get('AdapterRAM') or 0) / (1024 * 1024), 0)
                })
        except Exception:
            pass
        return json.dumps({
            'success': True,
            'primary_width': width,
            'primary_height': height,
            'displays': displays,
            'message': f'Primary screen: {width}x{height}'
        })
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Failed to get screen info: {str(e)}'})


# ============== Reminders / Tasks ==============

def create_reminder(title: str, body: str = "", due_date: str = "") -> str:
    """
    Create a Windows task/reminder using Task Scheduler or a toast notification.

    Args:
        title: Reminder title
        body: Reminder description
        due_date: Due date string (e.g. "2024-12-25 10:00")
    """
    try:
        # Show a toast notification as immediate reminder
        ps_script = f"""
$title = @'
{title}
'@
$msg = @'
{body}
'@
Add-Type -AssemblyName System.Windows.Forms
$notify = New-Object System.Windows.Forms.NotifyIcon
$notify.Icon = [System.Drawing.SystemIcons]::Information
$notify.Visible = $true
$notify.BalloonTipTitle = $title.Trim()
$notify.BalloonTipText = $msg.Trim()
$notify.BalloonTipIcon = "Info"
$notify.ShowBalloonTip(5000)
Start-Sleep -Seconds 6
$notify.Dispose()
Write-Output "success"
"""
        result = run_powershell(ps_script)

        # Also add to Windows Task Scheduler if due_date provided
        if due_date:
            try:
                dt = None
                for fmt in ('%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
                    try:
                        dt = datetime.strptime(due_date, fmt)
                        break
                    except ValueError:
                        continue
                if dt:
                    trigger_time = dt.strftime('%Y-%m-%dT%H:%M:%S')
                    task_script = f"""
$action = New-ScheduledTaskAction -Execute 'msg' -Argument "* {title.replace("'", "")}"
$trigger = New-ScheduledTaskTrigger -Once -At '{trigger_time}'
Register-ScheduledTask -TaskName 'FunctionWin_{title[:20].replace(" ","_")}' -Action $action -Trigger $trigger -Force
"""
                    run_powershell(task_script)
            except Exception:
                pass

        return json.dumps({'success': True, 'message': f'Reminder created: "{title}"'})
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Failed to create reminder: {str(e)}'})


# ============== Wi-Fi ==============

def get_wifi_networks() -> str:
    """Get available Wi-Fi networks."""
    try:
        result = run_shell_command('netsh wlan show networks mode=bssid')
        if "Error" in result or not result:
            return json.dumps({'success': False, 'error': 'Could not scan Wi-Fi networks. Make sure Wi-Fi is enabled.'})

        networks = []
        current = {}
        for line in result.splitlines():
            line = line.strip()
            if line.startswith('SSID') and 'BSSID' not in line:
                if current:
                    networks.append(current)
                ssid = line.split(':', 1)[-1].strip()
                current = {'ssid': ssid}
            elif 'Signal' in line:
                current['signal'] = line.split(':', 1)[-1].strip()
            elif 'Authentication' in line:
                current['security'] = line.split(':', 1)[-1].strip()
            elif 'Network type' in line:
                current['type'] = line.split(':', 1)[-1].strip()
        if current:
            networks.append(current)

        # Get current connection
        current_conn = run_shell_command('netsh wlan show interfaces')
        connected_ssid = ""
        for line in current_conn.splitlines():
            if 'SSID' in line and 'BSSID' not in line:
                connected_ssid = line.split(':', 1)[-1].strip()
                break

        for n in networks:
            n['connected'] = n.get('ssid') == connected_ssid

        return json.dumps({
            'success': True,
            'count': len(networks),
            'networks': networks,
            'connected_to': connected_ssid,
            'message': f'Found {len(networks)} Wi-Fi networks'
        })
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Failed to get Wi-Fi networks: {str(e)}'})


# ============== Media Control ==============

def control_music(action: str) -> str:
    """
    Control media playback using Windows media keys.

    Args:
        action: "play", "pause", "play_pause", "next", "previous", "stop"
    """
    try:
        VK_MAP = {
            'play': 0xB3,
            'pause': 0xB3,
            'play_pause': 0xB3,
            'next': 0xB0,
            'previous': 0xB1,
            'stop': 0xB2,
        }
        action_lower = action.lower()
        if action_lower not in VK_MAP:
            return json.dumps({'success': False, 'error': f'Unknown action: {action}. Use: play, pause, next, previous, stop'})

        vk = VK_MAP[action_lower]
        # Send media key via keybd_event
        ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
        time.sleep(0.05)
        ctypes.windll.user32.keybd_event(vk, 0, 2, 0)  # key up

        return json.dumps({'success': True, 'message': f'Media action "{action}" sent'})
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Failed to control media: {str(e)}'})


# ============== Math & Data ==============

def calculate_expression(expression: str) -> str:
    """Safely evaluate a mathematical expression."""
    try:
        if len(expression) > 500:
            return json.dumps({'success': False, 'error': 'Expression too long'})
        allowed_names = {k: v for k, v in math.__dict__.items() if not k.startswith('_')}
        allowed_names.update({'abs': abs, 'round': round, 'min': min, 'max': max, 'sum': sum})
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return json.dumps({'success': True, 'expression': expression, 'result': result, 'message': f'{expression} = {result}'})
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Calculation error: {str(e)}'})


def analyze_data(data_type: str, numbers: List[float]) -> str:
    """Perform statistical analysis on a list of numbers."""
    try:
        arr = np.array(numbers)
        result = {
            'success': True,
            'data_type': data_type,
            'count': len(numbers),
            'sum': float(np.sum(arr)),
            'mean': float(np.mean(arr)),
            'median': float(np.median(arr)),
            'std': float(np.std(arr)),
            'variance': float(np.var(arr)),
            'min': float(np.min(arr)),
            'max': float(np.max(arr)),
            'range': float(np.max(arr) - np.min(arr)),
            'percentile_25': float(np.percentile(arr, 25)),
            'percentile_75': float(np.percentile(arr, 75)),
        }
        return json.dumps(result)
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Analysis error: {str(e)}'})


# ============== QR Code ==============

def generate_qr_code(text: str, save_path: str = r"~\Desktop\qr_code.png") -> str:
    """Generate a QR code image."""
    try:
        import qrcode
        expanded_path = os.path.expanduser(save_path)
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(expanded_path)
        return json.dumps({'success': True, 'path': expanded_path, 'message': f'QR code saved to {expanded_path}'})
    except ImportError:
        return json.dumps({'success': False, 'error': 'qrcode library not installed. Run: pip install qrcode[pil]'})
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Failed to generate QR code: {str(e)}'})


# ============== Text File ==============

def process_text_file(file_path: str, operation: str) -> str:
    """
    Process a text file with various operations.

    Args:
        file_path: Path to the text file
        operation: "read", "word_count", "line_count", "summary", "uppercase", "lowercase"
    """
    try:
        expanded_path = os.path.expanduser(file_path)
        if not os.path.exists(expanded_path):
            return json.dumps({'success': False, 'error': f'File not found: {expanded_path}'})

        with open(expanded_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        op = operation.lower()
        if op == 'read':
            return json.dumps({'success': True, 'content': content[:5000], 'message': 'File read successfully'})
        elif op == 'word_count':
            words = len(content.split())
            return json.dumps({'success': True, 'word_count': words, 'message': f'Word count: {words}'})
        elif op == 'line_count':
            lines = len(content.splitlines())
            return json.dumps({'success': True, 'line_count': lines, 'message': f'Line count: {lines}'})
        elif op == 'summary':
            lines = content.splitlines()
            return json.dumps({
                'success': True,
                'lines': len(lines),
                'words': len(content.split()),
                'characters': len(content),
                'first_100_chars': content[:100],
                'message': f'File summary: {len(lines)} lines, {len(content.split())} words'
            })
        elif op == 'uppercase':
            out_path = expanded_path.replace('.txt', '_upper.txt')
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(content.upper())
            return json.dumps({'success': True, 'output_path': out_path, 'message': f'Uppercase version saved to {out_path}'})
        elif op == 'lowercase':
            out_path = expanded_path.replace('.txt', '_lower.txt')
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(content.lower())
            return json.dumps({'success': True, 'output_path': out_path, 'message': f'Lowercase version saved to {out_path}'})
        else:
            return json.dumps({'success': False, 'error': f'Unknown operation: {operation}'})
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Error processing file: {str(e)}'})


# ============== Date/Time ==============

def get_current_datetime() -> str:
    """Get the current date and time."""
    try:
        now = datetime.now()
        return json.dumps({
            'success': True,
            'datetime': now.strftime('%Y-%m-%d %H:%M:%S'),
            'date': now.strftime('%Y-%m-%d'),
            'time': now.strftime('%H:%M:%S'),
            'day_of_week': now.strftime('%A'),
            'timestamp': int(now.timestamp()),
            'message': f'Current date/time: {now.strftime("%A, %B %d %Y at %H:%M:%S")}'
        })
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Failed to get datetime: {str(e)}'})


# ============== Windows-Specific Extras ==============

def lock_screen() -> str:
    """Lock the Windows screen."""
    try:
        ctypes.windll.user32.LockWorkStation()
        return json.dumps({'success': True, 'message': 'Screen locked'})
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Failed to lock screen: {str(e)}'})


def show_notification(title: str, message: str) -> str:
    """Show a Windows toast notification."""
    try:
        ps_script = f"""
$title = @'
{title}
'@
$msg = @'
{message}
'@
Add-Type -AssemblyName System.Windows.Forms
$notify = New-Object System.Windows.Forms.NotifyIcon
$notify.Icon = [System.Drawing.SystemIcons]::Information
$notify.Visible = $true
$notify.BalloonTipTitle = $title.Trim()
$notify.BalloonTipText = $msg.Trim()
$notify.BalloonTipIcon = "Info"
$notify.ShowBalloonTip(4000)
Start-Sleep -Seconds 5
$notify.Dispose()
"""
        run_powershell(ps_script)
        return json.dumps({'success': True, 'message': f'Notification shown: "{title}"'})
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Failed to show notification: {str(e)}'})


def set_wallpaper(image_path: str) -> str:
    """Set the desktop wallpaper."""
    try:
        expanded_path = os.path.expanduser(image_path)
        if not os.path.exists(expanded_path):
            return json.dumps({'success': False, 'error': f'Image file not found: {expanded_path}'})
        SPI_SETDESKWALLPAPER = 20
        ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, expanded_path, 3)
        return json.dumps({'success': True, 'message': f'Wallpaper set to: {expanded_path}'})
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Failed to set wallpaper: {str(e)}'})


def get_installed_apps() -> str:
    """Get a list of installed applications from the registry."""
    try:
        ps_script = """
Get-ItemProperty HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* |
  Where-Object {$_.DisplayName} |
  Select-Object DisplayName, DisplayVersion, Publisher |
  Sort-Object DisplayName |
  ConvertTo-Json -Compress
"""
        result = run_powershell(ps_script)
        try:
            apps = json.loads(result)
        except json.JSONDecodeError:
            return json.dumps({'success': False, 'error': f'Failed to parse app list: {result[:200]}'})
        if isinstance(apps, dict):
            apps = [apps]
        simplified = [{'name': a.get('DisplayName', ''), 'version': a.get('DisplayVersion', ''), 'publisher': a.get('Publisher', '')} for a in apps]
        return json.dumps({'success': True, 'count': len(simplified), 'apps': simplified[:100], 'message': f'Found {len(simplified)} installed apps'})
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Failed to list apps: {str(e)}'})


def empty_recycle_bin() -> str:
    """Empty the Windows Recycle Bin."""
    try:
        ps_script = "Clear-RecycleBin -Force -ErrorAction SilentlyContinue; Write-Output 'success'"
        result = run_powershell(ps_script)
        return json.dumps({'success': True, 'message': 'Recycle Bin emptied'})
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Failed to empty Recycle Bin: {str(e)}'})


def get_network_info() -> str:
    """Get network interface information."""
    try:
        ps_script = "Get-NetIPAddress | Where-Object {$_.AddressFamily -eq 'IPv4'} | Select-Object InterfaceAlias,IPAddress,PrefixLength | ConvertTo-Json"
        result = run_powershell(ps_script)
        try:
            interfaces = json.loads(result)
        except json.JSONDecodeError:
            return json.dumps({'success': False, 'error': f'Failed to parse network info: {result[:200]}'})
        if isinstance(interfaces, dict):
            interfaces = [interfaces]
        net_io = psutil.net_io_counters()
        return json.dumps({
            'success': True,
            'interfaces': interfaces,
            'bytes_sent_mb': round(net_io.bytes_sent / (1024 * 1024), 2),
            'bytes_recv_mb': round(net_io.bytes_recv / (1024 * 1024), 2),
            'message': f'Found {len(interfaces)} network interface(s)'
        })
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Failed to get network info: {str(e)}'})


# ============== Execute any function by name ==============

def execute_function(function_name: str, parameters: Dict[str, Any] = None) -> str:
    """Execute any available function by name with given parameters."""
    if function_name not in AVAILABLE_FUNCTIONS:
        return json.dumps({'success': False, 'error': f'Function "{function_name}" not found'})
    try:
        func = AVAILABLE_FUNCTIONS[function_name]
        if parameters:
            result = func(**parameters)
        else:
            result = func()
        return result
    except Exception as e:
        return json.dumps({'success': False, 'error': f'Error executing {function_name}: {str(e)}'})


# ============== Available Functions Registry ==============

AVAILABLE_FUNCTIONS = {
    # Helpers
    'run_powershell': run_powershell,
    'run_shell_command': run_shell_command,

    # Screenshot & Clipboard
    'take_screenshot': take_screenshot,
    'copy_to_clipboard': copy_to_clipboard,
    'get_clipboard_content': get_clipboard_content,
    'paste_from_clipboard': paste_from_clipboard,

    # Theme
    'change_theme': change_theme,
    'get_current_theme': get_current_theme,

    # Audio
    'set_volume': set_volume,
    'get_volume': get_volume,
    'mute_volume': mute_volume,
    'unmute_volume': unmute_volume,

    # Display
    'set_brightness': set_brightness,
    'get_brightness': get_brightness,

    # Focus / DND
    'enable_do_not_disturb': enable_do_not_disturb,
    'disable_do_not_disturb': disable_do_not_disturb,

    # Files
    'find_files': find_files,
    'open_file': open_file,
    'open_folder': open_folder,

    # System
    'get_battery_info': get_battery_info,
    'get_system_info': get_system_info,
    'get_cpu_usage': get_cpu_usage,
    'get_memory_usage': get_memory_usage,
    'get_disk_usage': get_disk_usage,

    # Apps
    'open_application': open_application,
    'quit_application': quit_application,
    'list_running_applications': list_running_applications,
    'get_installed_apps': get_installed_apps,

    # Mouse & Keyboard
    'click_at_coordinates': click_at_coordinates,
    'drag_mouse': drag_mouse,
    'type_text': type_text,
    'send_keyboard_shortcut': send_keyboard_shortcut,
    'scroll_screen': scroll_screen,
    'get_mouse_position': get_mouse_position,
    'get_screen_info': get_screen_info,

    # Productivity
    'create_reminder': create_reminder,

    # Network
    'get_wifi_networks': get_wifi_networks,
    'get_network_info': get_network_info,

    # Media
    'control_music': control_music,

    # Math & Data
    'calculate_expression': calculate_expression,
    'analyze_data': analyze_data,

    # Utilities
    'generate_qr_code': generate_qr_code,
    'process_text_file': process_text_file,
    'get_current_datetime': get_current_datetime,
    'execute_function': execute_function,

    # Windows Extras
    'lock_screen': lock_screen,
    'show_notification': show_notification,
    'set_wallpaper': set_wallpaper,
    'empty_recycle_bin': empty_recycle_bin,
}
