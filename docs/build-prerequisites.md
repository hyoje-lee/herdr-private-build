# 빌드·설치 전 확인 절차

코어와 앱의 필요한 항목을 각각 확인한 뒤 부족한 도구만 준비합니다. 실제 빌드·설치 순서는 [차단 빌드 안내](private-build.md)를 따릅니다. 아래 절차는 기존 실행 프로세스를 종료하거나 설정 파일을 덮어쓰지 않습니다.

## 1. 대상과 기준 소스 확인

코어만 필요한 서버에는 GUI 라이브러리가 필요하지 않습니다. 데스크톱 앱은 차단 빌드 코어를 먼저 설치한 뒤 준비합니다. 현재 설치 스크립트는 Linux x86_64·aarch64를 지원합니다.

```sh
uname -sm
git status --short
git submodule status --recursive
```

필요한 소스가 초기화되지 않았다면 해당 구성요소만 받습니다. 기존 submodule에 작업 중인 변경이 있으면 먼저 확인하고, 초기화 명령으로 덮어쓰지 않습니다.

```sh
# 코어를 준비할 때
git submodule update --init --recursive herdr-core

# 앱을 준비할 때
git submodule update --init --recursive herdr-app
```

요구 버전을 확인할 때에는 최신 인터넷 예제보다 **고정된 소스의 빌드 정의와 CI**를 먼저 읽습니다. 소스가 갱신되면 다음 파일을 다시 조사합니다.

| 확인 대상 | 코어 | 앱 |
| --- | --- | --- |
| Rust·Zig 기준 | [CI](../herdr-core/.github/workflows/ci.yml), [README](../herdr-core/README.md) | [CI](../herdr-app/.github/workflows/ci.yml), [README](../herdr-app/README.md) |
| native 라이브러리 빌드 | [ghostty-vt/build.rs](../herdr-core/crates/ghostty-vt/build.rs) | [ghostty-sys/build.rs](../herdr-app/crates/ghostty-sys/build.rs) |
| Rust 의존성과 잠금 파일 | [Cargo.toml](../herdr-core/Cargo.toml), [Cargo.lock](../herdr-core/Cargo.lock) | [Cargo.toml](../herdr-app/Cargo.toml), [Cargo.lock](../herdr-app/Cargo.lock) |
| 설치 경로와 부수 효과 | [원본 설치 스크립트](../herdr-core/scripts/install-local.sh) | [원본 설치 스크립트](../herdr-app/scripts/install-linux) |

원본 설치 스크립트는 조사 자료입니다. 이 작업 공간에서는 차단 정책을 적용하는 별도 스크립트를 사용합니다. 소스 리비전과 패치 문맥 검사를 우회하거나, 빌드를 통과시키려고 버전 고정값만 바꾸지 않습니다.

## 2. 필요한 도구 구분

| 항목 | 코어 | 앱 |
| --- | --- | --- |
| Git·tar·Python 3.10 이상 | 필요합니다. | 필요합니다. |
| Rust·Cargo | 기준은 Rust 1.95.0이며, 스크립트는 1.95.0 이상을 검사합니다. | 같습니다. |
| Zig | 0.16.0이 필요합니다. | 0.16.0이 필요합니다. |
| C/C++ 빌드 도구 | 필요합니다. | 필요합니다. |
| clang·공유 libclang·pkg-config | 현재 코어 빌드에서는 별도로 요구하지 않습니다. | bindgen과 GUI 의존성에 필요합니다. |
| XCB·xkbcommon·Wayland·Vulkan·fontconfig·freetype 개발 파일 | 필요하지 않습니다. | 필요합니다. |
| 설치된 차단 빌드 코어 | 필요하지 않습니다. | 앱 설치·실행에 필요합니다. 앱만 `--build-only`로 빌드할 때에는 필요하지 않습니다. |
| SSH 클라이언트·원격 접속 권한 | 원격 머신 기능을 사용할 때 필요합니다. | 연결한 코어가 사용하는 조건을 확인합니다. |
| X11/Wayland 세션과 그래픽 드라이버 | 필요하지 않습니다. | 실제 GUI 실행·검증에 필요합니다. |

```sh
command -v git tar python3 cargo rustc zig cc c++
python3 --version
rustc --version
cargo --version
zig version
```

앱은 추가로 확인합니다.

```sh
command -v clang pkg-config
pkg-config --modversion xcb xkbcommon xkbcommon-x11 wayland-client \
  vulkan fontconfig freetype2
```

`clang` 실행 파일만 있다고 bindgen이 사용할 `libclang`이 있는 것은 아닙니다. 앱의 `--check`는 공유 libclang을 로드할 수 있는지도 확인합니다. 표준 경로가 아닌 곳에 설치했다면 `LIBCLANG_PATH`를 확인합니다.

## 3. 자동 사전 검사

```sh
./scripts/build-install-core.sh --check
```

코어 설치 후 데스크톱 앱도 필요한 경우 검사합니다.

```sh
./scripts/build-install-app.sh --check
```

부족한 도구와 라이브러리를 출력하고 오류 코드로 종료합니다. 전제조건을 통과하면 대상 소스의 고정 리비전과 작업 트리도 검사합니다. 앱 검사는 같은 `--prefix`의 `bin/herdr-core`가 응답하는 `--private-build` 식별값을 확인합니다. 스크립트는 의존성 다운로드·빌드·설치 명령이나 데몬 시작 명령을 실행하지 않습니다. 버전 확인에 사용하는 도구 자체의 동작은 해당 도구의 설정을 따릅니다.

설치 경로를 바꿀 때에는 사전 검사와 설치, 코어와 앱에 동일한 `--prefix`·`--data-home`을 전달합니다. `--check`는 실제 전체 컴파일이나 GUI 동작을 보장하지 않습니다.

## 4. 부족한 도구 준비

배포판·아키텍처·권한을 확인한 뒤 적합한 패키지 관리자와 신뢰하는 배포처를 선택합니다. 시스템 패키지 설치에는 관리자 권한이 필요할 수 있습니다. 아래는 Ubuntu 계열의 예시이며, 두 구성요소에 필요한 패키지를 구분합니다.

```sh
# 코어 공통 도구
sudo apt-get install build-essential git python3

# 데스크톱 앱을 설치할 장비에만 추가합니다.
sudo apt-get install pkg-config clang libclang-dev \
  libxcb1-dev libxkbcommon-dev libxkbcommon-x11-dev libwayland-dev \
  libvulkan-dev mesa-vulkan-drivers libfontconfig-dev libfreetype-dev
```

rustup을 사용하는 환경에서는 `rustup toolchain install 1.95.0 --profile minimal`로 기준 버전을 준비할 수 있습니다. 전역 기본 버전을 변경하지 않고 다음처럼 선택합니다.

```sh
RUSTUP_TOOLCHAIN=1.95.0 ./scripts/build-install-core.sh --check
RUSTUP_TOOLCHAIN=1.95.0 ./scripts/build-install-app.sh --check
```

Zig는 [공식 다운로드](https://ziglang.org/download/)에서 OS·아키텍처에 맞는 0.16.0 배포 파일과 SHA-256을 확인하고, `zig`가 PATH에 있도록 준비합니다. 별도 설치 경로를 사용한다면 `ZIG=/절대/경로/zig`를 지정할 수 있습니다. 사전 검사·빌드·manifest 모두 동일한 실행 파일을 사용합니다. Cargo와 Zig의 의존성 다운로드에는 허용된 네트워크·프록시·인증서 구성이 필요합니다. 프록시 인증정보나 전체 환경변수는 문서에 복사하지 않습니다.

## 5. 설치 위치와 실행 상태 확인

```sh
command -v herdr-core hc herdr-app
herdr-core --version
herdr-app --version
df -h . "$HOME/.local"
free -h
```

명령이 없는 경우에는 아직 설치되지 않은 것으로 구분합니다. 설치하려는 데이터·실행 파일 경로의 쓰기 권한, 여유 디스크, 빌드 동시 작업 수를 확인합니다. 충분한 공간과 메모리가 필요한 이유는 원본 복사본, 두 구성요소의 독립 빌드 산출물, 기존 설치 백업을 함께 보관하기 때문입니다. 제한된 환경에서는 `--jobs 1` 또는 `--jobs 2`를 사용합니다.

실행 중인 기존 앱과 코어는 자동으로 중지하지 않습니다. 설치 전에 기존 터미널을 정리하고 앱과 코어를 정상 종료할 시점을 결정합니다. 설정은 기존 `~/.config/herdr-app/`을 그대로 사용합니다.

장비별 확인 결과와 부족한 항목은 `docs/local-history/YYYY-MM-DD.md`에 기록하고, 다른 환경에서도 필요한 절차 변경만 공유 문서에 반영합니다.
