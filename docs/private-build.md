# 외부 통계·업데이트 통신을 차단한 빌드

이 빌드는 Herdr 자체의 통계 수집·전송, 피드백 전송, 업데이트 확인·다운로드·적용을 비활성화합니다. SSH 원격 머신 연결과 터미널에서 사용자가 실행하는 Claude Code·Codex 등의 통신은 유지합니다. 감사 범위와 제한은 [소스 검토](source-audit.md)에 있습니다.

## 빌드와 설치

먼저 [설치 전 확인 절차](build-prerequisites.md)에 따라 사용할 구성요소의 도구·라이브러리·기존 설치 상태를 확인합니다. Linux x86_64 또는 aarch64에서 코어와 앱을 **각각 별도의 명령으로** 빌드·설치합니다.

```sh
# 코어만 빌드·설치합니다.
./scripts/build-install-core.sh
```

데스크톱 앱이 필요한 장비에서는 코어 설치를 확인한 뒤 별도로 실행합니다. 원격 서버 등 코어만 필요한 장비에서는 앱을 설치하지 않아도 됩니다.

```sh
# 앱만 빌드·설치합니다. 이미 설치한 차단 빌드 코어를 사용합니다.
./scripts/build-install-app.sh
```

각 스크립트는 해당 구성요소와 그 Ghostty 소스만 `.build/private/`로 복사하고 차단 패치를 적용합니다. 해당 구성요소의 release 빌드와 정책 테스트를 통과한 바이너리만 공식 배포와 같은 위치에 설치합니다. 코어 설치에는 앱 소스·GUI 라이브러리가 필요하지 않으며, 앱 설치는 코어를 다시 빌드하거나 변경하지 않습니다.

원본 submodule은 수정하지 않습니다. 소스 리비전이나 패치 문맥이 다르면 중단하며, 공식 배포 바이너리로 대체하지 않습니다. 빌드 의존성 다운로드는 허용됩니다. 시스템 도구·패키지는 [전제조건 문서](build-prerequisites.md)를 확인한 뒤 준비합니다. 스크립트는 `sudo`를 실행하거나 시스템 패키지를 임의로 변경하지 않습니다.

주요 옵션은 다음과 같습니다.

| 옵션 | 동작 |
| --- | --- |
| `--check` | 해당 구성요소의 도구·버전·라이브러리·소스 리비전을 검사합니다. 앱 설치 검사에는 설치된 차단 빌드 코어도 필요합니다. 빌드·설치는 하지 않습니다. |
| `--prepare-only` | 소스 복사와 패치만 수행해 적용 결과를 검토할 수 있습니다. |
| `--build-only` | 빌드와 정책 테스트까지 수행하고 설치하지 않습니다. |
| `--jobs 2` | 메모리에 맞춰 동시 빌드 수를 조절합니다. 기본값은 최대 4입니다. |
| `--prefix /절대/경로` | 바이너리를 해당 경로의 `bin/`에 설치합니다. 기본값은 `~/.local`입니다. 코어와 앱에 같은 값을 사용합니다. |
| `--data-home /절대/경로` | 데스크톱 실행 항목·아이콘·백업·빌드 기록 위치를 지정합니다. 기본값은 `XDG_DATA_HOME` 또는 `~/.local/share`입니다. |
| `--offline` | Cargo를 `--frozen`으로 실행합니다. Zig 패키지도 캐시에 있어야 합니다. 이 옵션은 OS 수준의 네트워크 격리가 아닙니다. |

## 설치 후 사용하는 환경

- 코어 스크립트는 `~/.local/bin/herdr-core`와 이를 가리키는 `hc` 링크를 설치합니다. 앱 스크립트는 `~/.local/bin/herdr-app`, `herdr-app.desktop` 실행 항목과 아이콘을 설치합니다. 패치된 앱은 같은 폴더의 `herdr-core`만 사용하므로, 앱 스크립트는 그 코어가 차단 빌드인지 확인한 뒤 진행합니다.
- 설정은 공식 앱과 같은 `~/.config/herdr-app/`을 그대로 사용합니다. 기존 단축키·모드·설정을 옮길 필요가 없습니다. 차단은 바이너리에 들어 있으므로 [통계·업데이트 설정](configuration.md)의 `telemetry`나 `HERDR_RELEASES_URL` 설정에 의존하지 않습니다.
- 덮어쓴 기존 파일과 심볼릭 링크는 `~/.local/share/herdr-build/backups/<구성요소>-<시각>/`에 보존하고, `restore.json`에 원래 경로와 백업 대응 관계를 기록합니다. 설치 중 실패하면 이번에 바꾼 파일을 자동으로 되돌립니다. 현재 설치본의 소스 리비전, 패치와 바이너리 SHA-256은 `~/.local/share/herdr-build/<core|app>/`의 `manifest.json`과 `private.patch`에 남습니다.
- 공식 앱 폴더 `~/.local/share/herdr-app/`은 지우지 않습니다. 설치 후 동작을 확인한 뒤 필요하면 직접 정리합니다.
- 설치 전에 공식 실행 파일을 직접 지우지 않습니다. 지운 뒤 설치하면 `restore.json`의 백업이 모두 `null`이 되어 이 기록으로는 공식 설치본을 되돌릴 수 없습니다. 미리 정리해야 한다면 해당 파일을 별도로 백업합니다.
- 실행 중인 앱과 코어를 자동으로 종료하거나 재시작하지 않습니다. 이미 실행 중인 공식 프로세스의 통신은 소급해서 차단되지 않으므로, 설치 전에 공식 앱과 코어를 정상 종료하고 설치 후 다시 시작합니다.
- 설치 후에는 [공식 설치 스크립트](setup.md#새-환경에서-수행할-순서)를 실행하지 않습니다. 이 스크립트는 `~/.local/bin/herdr-app`와 `herdr-app.desktop`을 공식 앱으로 다시 작성합니다. 이미 실행했다면 앱 스크립트를 다시 실행해 복구합니다.

설치 파일을 되돌리려면 앱과 코어를 정상 종료한 뒤 `restore.json`에 기록된 파일을 원래 위치에 복원합니다. 백업이 `null`인 항목은 이번 설치가 새로 만든 파일입니다. 이후 수정한 파일이 있다면 먼저 비교합니다.

## SSH와 모드

SSH 연결과 원격 터미널은 유지합니다. 같은 OS·CPU의 원격 호스트에 코어를 설치할 때에는 현재 패치된 코어가 복사됩니다. 다른 OS·CPU의 공식 코어를 내려받는 경로는 차단하므로, 해당 호스트에서 지원되는 보안 빌드를 먼저 준비해야 합니다. 이미 설치된 원격 코어에 연결한다고 그 코어의 보안 정책까지 바뀌지는 않습니다.

OS나 CPU가 다른 원격 호스트는 그 호스트에 이 저장소를 받아 코어만 빌드합니다. 앱 소스와 GUI 라이브러리는 필요하지 않습니다. 원격 호스트에서 다음을 실행합니다.

```sh
git submodule update --init --recursive herdr-core
./scripts/build-install-core.sh --check
./scripts/build-install-core.sh
~/.local/bin/herdr-core --private-build
```

설치 스크립트는 실행 중인 원격 코어를 재시작하지 않습니다. 기존 프로세스는 덮어쓰기 전의 바이너리로 계속 실행되며, Linux에서는 `/proc/<pid>/exe`가 `(deleted)`로 표시됩니다. `hc server status`의 `live`로 실행 중인 터미널을 확인한 뒤 원격 호스트에서 `hc server restart`를 실행합니다. 재시작하면 실행 중인 원격 프로그램이 종료되고, keep으로 설정한 터미널은 새 셸로 다시 열립니다.

설치된 코어는 시스템의 libc와 libgcc_s만 사용합니다. 다시 빌드할 계획이 없다면 설치 후 `.build/private/`, Zig 캐시, Rust·Zig 도구를 지워도 실행에는 영향이 없습니다. 다시 빌드할 때에는 [전제조건](build-prerequisites.md)을 다시 준비합니다.

기본 모드의 직접 HTTP·TCP·WebSocket 권한과 Git 의존성 자동 다운로드는 차단합니다. 모드의 `herdr.exec`·`herdr.hc`, 사용자가 지정하는 실행 프로그램과 SSH는 유지됩니다. 따라서 임의의 외부 모드를 안전하게 격리하는 샌드박스는 아닙니다. 보안 환경에서는 사용하는 모드와 실행 명령도 검토해야 합니다.

외부 예제 모드는 자동 설치하지 않습니다. 특히 `threads` 예제에는 `gh pr list`를 주기적으로 실행하는 기능이 있으므로, 자동 외부 질의를 원하지 않는 환경에서는 그대로 복사하지 않습니다. 자세한 근거는 [소스 검토](source-audit.md)에 있습니다.

## 검증

```sh
python3 -m unittest discover -s scripts -p 'test_secure_build.py'
./scripts/build-install-core.sh --prepare-only
./scripts/build-install-app.sh --prepare-only
git diff --check
git submodule foreach --recursive 'git status --short'
```

루트 `.venv`가 있다면 Python 검사 전에 `source .venv/bin/activate`를 실행합니다.

실제 빌드 과정은 코어의 라이브러리 테스트와 앱의 바이너리 테스트 중 `private_policy_`만 실행합니다. 전송 URL을 강제로 지정하고 가짜 `curl`을 PATH 앞에 배치해, 전송 경로가 실행되면 설치를 중단합니다. 앱·코어의 `--private-build` 식별값도 검사합니다. 이 검사는 전체 GUI·SSH 통합 검증을 대신하지 않습니다.

설치 후에는 PATH에서 찾는 실행 파일이 차단 빌드인지 확인합니다. 두 명령 모두 `herdr-private-v1`을 출력해야 하며, 공식 바이너리는 이 값을 출력하지 않습니다. 앱을 실행한 뒤에는 `herdr-app status`의 `errors`가 비어 있는지 확인합니다.

```sh
command -v herdr-core hc herdr-app
herdr-core --private-build
herdr-app --private-build
```

실제 적용 환경에서는 GUI를 실행해 통계와 업데이트가 비활성 상태인지, 기본 단축키와 SSH 연결이 동작하는지 확인합니다. 외부 통신을 관찰할 때에는 Herdr 자체 요청과 SSH·사용자 프로그램의 요청을 구분하고, 프롬프트나 코드가 포함될 수 있는 패킷 본문을 공유 문서에 기록하지 않습니다.
