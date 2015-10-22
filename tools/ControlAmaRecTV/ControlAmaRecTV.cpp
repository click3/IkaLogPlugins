
#include <string>
#include <vector>
#include <algorithm>
#include <iostream>

#include <Windows.h>
#include <tlhelp32.h>

#include <boost/filesystem.hpp>
#include <boost/filesystem/fstream.hpp>
#include <boost/format.hpp>


// 試合終了後8人のスコアが表示された瞬間から録画停止するまでの待ち時間(単位ミリ秒)
const unsigned int WAIT_STOP_MILLIS = 15 * 1000;

// 録画停止から録画ファイルリネームを試みるまでの待ち時間(単位ミリ秒)
const unsigned int WAIT_RENAME_MILLIS = 10 * 1000;

// 録画開始/停止のホットキーを押下してから話すまでの待ち時間(単位ミリ秒)
const unsigned int WAIT_KEY_UP_MILLIS = 16;

// 録画開始終了などを指示するのに使うホットキー
// アルファベットは大文字で一文字、特殊キーはWinUser.hのVK_から始まる定数を使用できる
// 複数指定で同時押し
// ex. 「Ctrl+z」は「VK_CONTROL, 'Z'」、「F7」は「VK_F7」
const unsigned int HOT_KEYS[] = {
  VK_CONTROL, 'Z',
};


unsigned int GetScanCode(const unsigned int virtualKeyCode) {
  return ::MapVirtualKeyExW(virtualKeyCode, MAPVK_VK_TO_VSC, NULL);
}
void PressKey(const unsigned int virtualKeyCode) {
  ::keybd_event(virtualKeyCode, GetScanCode(virtualKeyCode), 0, NULL);
}
void UpKey(const unsigned int virtualKeyCode) {
  ::keybd_event(virtualKeyCode, GetScanCode(virtualKeyCode), KEYEVENTF_KEYUP, NULL);
}
void SendHotKey() {
  for (const unsigned int key : HOT_KEYS) {
    PressKey(key);
  }
  Sleep(WAIT_KEY_UP_MILLIS);
  for (const unsigned int key : HOT_KEYS) {
    UpKey(key);
  }
}

std::wstring GetEnv(const wchar_t * const name) {
  wchar_t buf[32768];
  const unsigned int length = ::GetEnvironmentVariableW(name, buf, _countof(buf));
  if (length == 0) {
    return{};
  }
  return{ &buf[0], &buf[length] };
}
boost::filesystem::path GetDestDir() {
  return GetEnv(L"IKALOG_MP4_DESTDIR");
}
boost::filesystem::path GetDestFilename() {
  return GetEnv(L"IKALOG_MP4_DESTNAME");
}
boost::filesystem::path GetDestPath() {
  const auto filename = GetDestFilename();
  if (filename.empty()) {
    return{};
  }
  boost::filesystem::path path = GetDestDir() / filename;
  path.replace_extension(".avi");
  return path;
}

std::vector<std::wstring> GetWindowTitleList() {
  std::vector<std::wstring> result;
  ::EnumWindows([](const HWND handle, const LPARAM resultPtr) -> BOOL {
    wchar_t buf[4096];
    const unsigned int length = ::GetWindowTextW(handle, buf, _countof(buf));
    reinterpret_cast<std::vector<std::wstring>*>(resultPtr)->push_back({ &buf[0], &buf[length] });
    return TRUE;
  }, reinterpret_cast<LPARAM>(&result));
  return result;
}
std::wstring GetAmaRecTvTitle() {
  const std::vector<std::wstring> all = GetWindowTitleList();
  std::vector<std::wstring> amarecList(all.size());
  const auto it = std::copy_if(all.begin(), all.end(), amarecList.begin(), [](const std::wstring &title) {
    if (title.length() < 10) {
      return false;
    }
    return title.substr(0, 10) == L"AmaRecTV  ";
  });
  amarecList.resize(std::distance(amarecList.begin(), it));
  if (amarecList.empty()) {
    return{};
  }
  std::sort(amarecList.begin(), amarecList.end());
  return amarecList.back();
}
boost::filesystem::path GetSrcDir() {
  return GetDestDir();
}
boost::filesystem::path GetSrcPath() {
  const std::wstring title = GetAmaRecTvTitle();
  if (title.empty() || title.length() < 15 || title.substr(title.length() - 4, 4) != L".avi") {
    return{};
  }
  return GetSrcDir() / title.substr(10);
}

bool IsFileExclusiveLock(const boost::filesystem::path &path) {
  if (path.empty() || !boost::filesystem::is_regular_file(path)) {
    return false;
  }
  const HANDLE handle = ::CreateFileW(path.wstring().c_str(), GENERIC_WRITE, FILE_SHARE_WRITE | FILE_SHARE_READ, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
  if (handle == INVALID_HANDLE_VALUE) {
    return true;
  }
  ::CloseHandle(handle);
  return false;
}
bool IsRecording() {
  return IsFileExclusiveLock(GetSrcPath());
}

void WriteDebugLog() {
  boost::filesystem::wofstream ofs(L"debug.log", std::ios::app);
  ofs << boost::wformat(L"----\n");
  ofs << boost::wformat(L"commandline: %s\n") % ::GetCommandLineW();
  const wchar_t * const envNameList[] = {
    L"IKALOG_MP4_DESTDIR", L"IKALOG_MP4_DESTNAME", L"IKALOG_STAGE", L"IKALOG_RULE", L"IKALOG_WON"
  };
  for (const wchar_t * const envName : envNameList) {
    ofs << boost::wformat(L"%s: %s\n") % envName % GetEnv(envName);
  }
  ofs << boost::wformat(L"window title list:\n");
  for (const std::wstring &title : GetWindowTitleList()) {
    ofs << boost::wformat(L"\t%s\n") % title;
  }
  ofs << boost::wformat(L"AmaRecTV title: %s\n") % GetAmaRecTvTitle();
  ofs << boost::wformat(L"src path: %s\n") % GetSrcPath();
  ofs << boost::wformat(L"dest path: %s\n") % GetDestPath();
  ofs << boost::wformat(L"is recording?: %s\n") % (IsRecording() ? L"true" : L"false");
  ofs << boost::wformat(L"----\n");
  ofs.close();
}

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
  std::locale loc = std::locale("japanese").combine<std::numpunct<char> >(std::locale::classic()).combine<std::numpunct<wchar_t> >(std::locale::classic());
  std::locale::global(loc);
  std::wcout.imbue(loc);
  std::cout.imbue(loc);

  //WriteDebugLog();

  int argc = 0;
  const wchar_t * const * const argv = ::CommandLineToArgvW(::GetCommandLineW(), &argc);
  if (argv == nullptr || argc != 2) {
    return 1;
  }
  const std::wstring op = argv[1];

  bool start;
  if (op == L"start") {
    start = true;
  } else if (op == L"stop") {
    start = false;
  } else {
    return 1;
  }

  if (start) {
    if (IsRecording()) {
      return 1;
    }
    SendHotKey();
    return 0;
  }
  if (!IsRecording()) {
    return 1;
  }
  ::Sleep(WAIT_STOP_MILLIS);
  SendHotKey();
  const boost::filesystem::path destPath = GetDestPath();
  if (!destPath.empty()) {
    ::Sleep(WAIT_RENAME_MILLIS);
    boost::filesystem::create_directories(destPath.parent_path());
    boost::filesystem::rename(GetSrcPath(), destPath);
  }
  return 0;
}
