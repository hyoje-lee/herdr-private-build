# 외부 통신 경로와 차단 정책

이 문서는 고정된 Herdr 소스에서 확인한 통신 경로와 로컬 빌드의 변경 이유를 설명합니다. 설치 방법은 [빌드 안내](private-build.md), 적용할 변환은 [secure_policy.py](../scripts/secure_policy.py)에 있습니다.

## 범위와 기준

| 원본 | 검토 기준 커밋 |
| --- | --- |
| herdr-core | `bb8a2f7740fd308e520e4e9361c292c993c7f08e` |
| herdr-app | `8e1208deeff2a24441a192974e648c6fa0c5053c` |
| 코어의 Ghostty | `1e5cdb865807abc990181efb8ebfa9122955cce2` |
| 앱의 Ghostty | `291fd050b9e9c293c8adb6a140742649b7e42d3a` |
| 외부 모드 예제 | `0ec967640bf854ffb839e9af06c1e0c328bc9815` |

앱·코어의 Rust 코드, 기본 제공 JavaScript 모드, vendored GPUI·QuickJS·Ghostty에서 HTTP 클라이언트, 소켓, URL, 다운로드 명령, 프로세스 실행과 모드 권한을 검색하고 호출 경로를 확인했습니다. 별도 리뷰 에이전트도 주요 전송 경로와 차단 구현을 검토했습니다. 문자열 검색 결과만으로 모든 코드의 안전성을 증명하거나, Cargo 의존성 전체에 대한 별도 보안 감사를 완료했다고 주장하지 않습니다.

보호 대상은 Herdr가 자체적으로 전송하는 사용 통계, 피드백 본문·스크린샷, 업데이트 관련 요청입니다. 사용자가 등록한 SSH 대상과 실행한 프로그램의 통신은 허용합니다. 빌드 의존성 다운로드도 허용합니다. 이 구분 때문에 전체 프로세스 트리를 네트워크에서 격리하는 방식은 적용하지 않습니다.

## 경로별 처리

| 기능과 소스 | 원본의 동작 | 차단 빌드 |
| --- | --- | --- |
| [통계](../herdr-app/src/telemetry.rs) | 사용량·시간·허용된 이름 등 집계값을 수집하고 POST합니다. 설정·환경변수·릴리스 빌드 여부가 영향을 줍니다. | 수집 시작, 설정 활성화, 전송 endpoint와 POST를 무조건 비활성화합니다. |
| [피드백](../herdr-app/src/feedback.rs) | 사용자가 선택한 텍스트와 스크린샷을 전송합니다. 소스 빌드도 환경변수로 전송할 수 있습니다. | endpoint를 없애고 POST 진입점에서도 거부합니다. |
| [업데이트](../herdr-app/src/update.rs) | 앱·코어 버전 확인, 다운로드, 변경 내역 조회, 재시작 시 대기 업데이트 적용을 수행합니다. | 확인 스레드, 수동 코어 갱신, 다운로드, 시작·종료 시 적용과 업데이트 후 코어 갱신을 차단합니다. |
| [업데이트 미디어](../herdr-app/src/update_notes.rs) | 변경 내역에 포함된 이미지·클립을 다운로드합니다. | 다운로드 함수를 비활성화합니다. |
| [코어 자동 설치](../herdr-app/src/core_bin.rs) | 코어가 없거나 호환되지 않으면 설치 스크립트를 받아 실행할 수 있습니다. Windows에서는 `irm .../core/install.ps1 \| iex`를 실행합니다. | 설치·갱신·번들 다운로드를 거부하고, 함께 설치한 차단 빌드 코어만 찾습니다. Linux에서는 앱과 같은 폴더의 `herdr-core`를, Windows에서는 upstream 배치에 맞춰 옆 폴더의 `herdr-core\herdr-core.exe`를 찾습니다. 코어는 별도 스크립트로 설치합니다. |
| [코어 릴리스](../herdr-core/crates/herdr-core/src/releases.rs) | 코어 갱신과 타 플랫폼 원격 설치에 필요한 manifest·패키지를 받습니다. | 다운로드 진입점에서 오류를 반환합니다. |
| [코어 로컬 갱신](../herdr-core/crates/herdr-core/src/cli/update.rs) | `hc update --from`으로 다른 바이너리를 적용할 수 있습니다. | 차단 정책이 없는 바이너리로 바뀌지 않도록 자체 갱신을 거부합니다. 재빌드는 설치 스크립트로 수행합니다. |
| [모드 권한](../herdr-app/src/mods.rs) | 직접 네트워크 접근과 명령 실행을 모두 허용합니다. | 직접 HTTP·TCP·WebSocket 권한을 거부합니다. 명시적인 명령 실행 기능은 유지합니다. |
| [모드 의존성](../herdr-app/vendor/gpui-kit/crates/shell/src/dependencies.rs) | 모드 로드 중 Git 의존성을 clone·fetch합니다. | Git 의존성을 선언한 모드를 거부합니다. 필요한 모듈은 검토 후 로컬에 포함해야 합니다. |
| [SSH 머신](../herdr-core/crates/herdr-core/src/machines.rs)·[원격 릴레이](../herdr-core/crates/herdr-core/src/remote.rs) | 등록한 머신에 연결하고 터미널·파일·명령을 전달합니다. | 유지합니다. 같은 OS·CPU에는 현재 패치된 코어를 복사하며, 다른 플랫폼의 공식 바이너리 자동 다운로드는 거부합니다. |
| [외부 threads 예제](../mods/sources/herdr-layout-examples/threads/mods/t4-threads/main.js) | `lookup()`이 주기적으로 `gh pr list`를 실행해 저장소·브랜치 정보를 GitHub에 질의합니다. | 설치 스크립트는 외부 예제 모드를 복사하지 않습니다. 다만 기존 앱 설정 폴더를 그대로 사용하므로 이미 설치한 모드는 계속 로드됩니다. 이 모드를 추가하려면 해당 자동 조회를 제거한 로컬 수정본을 사용해야 합니다. |

원본 통계 코드에서 터미널 본문·프롬프트·코드 내용을 직접 수집하는 로직은 확인되지 않았습니다. 그러나 피드백은 선택한 텍스트·이미지를 전송하고, 모드 실행 권한은 임의 프로그램을 실행할 수 있으므로 통계 설정만으로 전체 전송 위험을 판단해서는 안 됩니다.

일반 소스 빌드의 자동 업데이트 비활성화만으로는 부족합니다. 환경변수로 확인 동작을 다시 활성화할 수 있고, 대기 중인 업데이트 적용과 수동 갱신 경로도 있습니다. 패치는 이런 설정에 의존하지 않는 무조건 반환으로 처리하며, release 최적화 시 해당 실행 경로가 도달 불가능해집니다.

### Windows 경로

같은 고정 커밋에서 Windows 전용 코드(`cfg(windows)`, `platform/windows*.rs`)와 upstream Windows 설치 스크립트를 따로 검색했습니다. 위 표의 차단 지점은 OS 분기 바깥에 있어 Windows에도 그대로 적용됩니다. 이 검토는 소스 검색 결과이며, Windows 빌드에서 통신을 관찰해 확인하지는 않았습니다.

- 앱의 업데이트 다운로드(`curl_text`, `unpack`)는 Windows에서 System32의 `curl`을 직접 호출하지만, 두 함수 모두 진입점에서 반환합니다. 업데이트 후 재시작에 쓰는 `powershell` 호출은 통신하지 않습니다.
- 코어의 모든 릴리스 다운로드는 OS와 관계없이 `releases.rs`의 `curl()` 하나를 거치며, 이 함수가 차단돼 있습니다.
- Windows 코어에 함께 넣는 Microsoft ConPTY는 빌드할 때 upstream `scripts/fetch-conpty.ps1`이 GitHub에서 받습니다. 버전과 SHA-256이 고정돼 있어 빌드 의존성 다운로드로 취급합니다. Herdr가 실행 중에 보내는 통신은 아닙니다.
- WSL은 `hc machine add --via 'wsl.exe ...'`로 연결합니다. Windows와 OS가 다르므로 Windows 코어는 WSL에 공식 Linux 빌드를 설치하려 하고, 차단 빌드는 이를 거부합니다. WSL에는 차단 빌드 코어를 직접 설치해야 합니다.
- cargo-deny 설정에는 대상 플랫폼 제한이 없으므로, 취약점 검사는 Windows 전용 의존성도 포함합니다.
- **검증하지 않은 한계:** Linux 빌드는 정책 테스트 중 가짜 `curl`로 전송 시도를 잡아냅니다. Windows 빌드에는 이 검사가 없습니다. 정책 테스트가 확인하는 것은 차단 함수의 반환값뿐이며, 테스트 중에 `curl`이 호출되지 않았다는 사실은 확인하지 않습니다.

Windows에서만 필요한 설치 동작(PATH 레지스트리, 시작 메뉴 바로가기, MSVC·LLVM·SDK 검사, ConPTY 받기)은 [secure_windows.py](../scripts/secure_windows.py)에 있습니다. 고정 커밋, 패치, 취약점 검사, 빌드, 정책 테스트, 백업과 되돌리기는 두 OS가 [secure_build.py](../scripts/secure_build.py)의 같은 코드를 씁니다.

## 유지되는 기능과 신뢰 경계

- `herdr.exec`와 `herdr.hc`는 네트워크 사용이 가능한 프로그램을 실행하거나 코어에 작업을 요청할 수 있습니다. 악성 모드까지 격리하는 샌드박스가 아닙니다. 사용자 추가 모드와 프로그램 설정은 별도로 검토해야 합니다.
- `herdr-app check <폴더>`는 앱의 네트워크 차단 정책 대신 해당 폴더의 `gpui-shell.json`에 선언된 권한으로 모드를 로드합니다([근거](../herdr-app/vendor/gpui-kit/crates/shell/src/host.rs)의 `check`·`local_capabilities`). 이 파일에 네트워크 호스트를 선언한 모드는 검사 중에도 해당 호스트에 요청할 수 있습니다. 같은 모드가 앱에 설치되면 `herdr.exec`로도 외부 통신이 가능하므로 별도 패치 대신 모드 검토 규칙으로 관리합니다. 검토하지 않은 외부 모드는 `check`도 실행하지 않습니다.
- 사용자가 여는 링크는 외부 브라우저로 전달될 수 있습니다. 기본 모드의 직접 HTTP 요청과는 다른 경로이며, URL에 포함된 내용도 외부 전송으로 이어질 수 있습니다. 자동 실행 모드에서 이 기능을 사용하지 않는지 확인합니다.
- GPUI에는 HTTP 이미지 로더가 있으나, 이 기준 소스의 앱 초기화는 `NullHttpClient`를 사용하며 실제 HTTP 클라이언트로 교체하는 프로덕션 경로는 확인되지 않았습니다.
- Ghostty 전체 소스에는 Sentry 관련 코드가 있습니다. Herdr의 build.rs는 `-Demit-lib-vt`로 VT 라이브러리를 링크하므로 전체 Ghostty 앱의 통계 코드를 Herdr에서 실행 중인 통계로 간주하지 않습니다.
- SSH 대상에는 사용자 명령과 터미널 데이터가 전달됩니다. 원격 대상의 신뢰성과 설치된 코어가 적용한 정책도 별도로 확인해야 합니다.
- 이 정책은 동일 사용자 권한을 가진 악성 코드, 변경된 컴파일러·의존성, 취약점 악용까지 막는 OS 보안 경계나 보안 인증이 아닙니다. 중요 환경의 승인에는 실제 빌드 및 해당 환경에서의 통신 관찰이 필요합니다.

## 의존성 취약점 권고

현재 고정 커밋에 [cargo-deny 검사](private-build.md#의존성-취약점-검사)를 실행해 나온 권고와, 이를 검토한 결과입니다. 받아들인 권고는 ID와 사유를 [scripts/deny/app.toml](../scripts/deny/app.toml)에 기록했으므로 설치를 막지 않습니다. 목록에 없는 새 권고는 설치를 중단시킵니다.

- 코어에서는 권고가 나오지 않았습니다.
- 앱에서는 취약점 12건과 유지보수 중단 10건이 나왔고, yanked 크레이트 경고가 3건 있습니다. 22건 모두 위험을 받아들였습니다.
- rustls·rustls-webpki 취약점 5건은 모드 런타임 `gpui-shell`의 reqwest 클라이언트를 거쳐 들어옵니다. 이 클라이언트는 모드의 fetch·WebSocket·이미지 로딩에 쓰이며 모드의 네트워크 권한이 필요합니다. 차단 빌드는 기본 모드에 이 권한을 주지 않습니다. 다만 `herdr-app check`는 폴더의 `gpui-shell.json`에 선언된 권한을 줍니다(위 [신뢰 경계](#유지되는-기능과-신뢰-경계) 참고).
- rsa·crypto-bigint·ctutils·zstd·zstd-safe 취약점 6건은 모드 JS 런타임(quickjs-jit-stdlib, llrt)의 crypto·압축 모듈을 거쳐 들어옵니다. 모드 코드가 이 모듈을 호출할 때만 실행됩니다.
- zstd-sys 취약점 1건은 WebAssembly용 메모리 할당 shim에 있습니다. 이 shim은 wasm32 타깃에서만 빌드되므로 Linux·Windows 빌드와 관계없습니다(zstd-sys `build.rs`의 `need_wasm_shim`).
- 유지보수 중단 10건은 알려진 취약점이 없는 크레이트입니다.
- 위 경로가 차단 빌드에서 실제로 실행되지 않는지는 검증하지 않았습니다. 검토하지 않은 외부 모드를 쓰지 않는다는 [모드 검토 규칙](#유지되는-기능과-신뢰-경계)이 현재의 완화 수단입니다.

## 변경 시 재검토

`secure_policy.py`의 고정 커밋은 임의로 최신화하지 않습니다. 원본을 갱신할 때에는 위 경로, 새 네트워크 의존성, 기본 모드의 자동 실행 코드와 updater를 다시 검토합니다. 두 구성요소에 `--audit`을 실행해 새 권고는 검토하고, 해결된 권고는 `scripts/deny/`의 목록과 위 검토 기록에서 지웁니다. 문맥이 맞지 않는 패치를 생략하거나 무시하지 않습니다.

현재 `private_policy_` 테스트는 통계, 피드백, 앱 업데이트, 코어 다운로드만 실행합니다. 코어 자체 갱신(`cli/update.rs`), `core_bin`의 설치·갱신·번들 함수, `update_notes::fetch_media`, `update::after_update`는 무조건 반환 패치에만 의존합니다. 고정 커밋을 갱신할 때에는 이 차단 지점의 회귀 테스트를 함께 추가해, 같은 이름의 함수 밖에 새 전송 경로가 생겼는지 확인합니다. Windows 빌드에서는 가짜 `curl`로 호출을 잡지 못하므로, [Windows 경로](#windows-경로)도 함께 다시 검색합니다.

빌드·설치 검증은 [빌드 안내의 검증 절차](private-build.md#검증)를 따릅니다. [Cargo의 `--frozen` 설명](https://doc.rust-lang.org/cargo/commands/cargo.html)은 Cargo의 네트워크 동작에 관한 것이며, Zig나 임의 build script까지 OS 수준에서 격리한다는 뜻은 아닙니다.
