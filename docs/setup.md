# 설치와 재현

## 확인한 환경

2026-11-13에 이 장비에서 직접 확인한 값입니다. 아래 버전을 향후에도 최신 버전으로 간주하지 않습니다.

| 항목 | 확인한 값 |
| --- | --- |
| 운영체제 | Ubuntu 24.04.4 LTS, x86_64 |
| 데스크톱 앱 | `herdr-app 0.1.15` |
| 코어 | `hc 0.1.21` (`herdr-core --version`도 같은 값을 출력합니다.) |
| 모드 원본 | `https://github.com/herdrdev/herdr-layout-examples.git` |
| 모드 고정 커밋 | `0ec967640bf854ffb839e9af06c1e0c328bc9815` |

## 설치 경로

현재 장비는 다음 경로를 사용합니다. [v0.1.15 설치 스크립트](https://github.com/herdrdev/herdr-app/blob/v0.1.15/distribution/install.sh)도 함께 참고합니다.

| 경로 | 용도 |
| --- | --- |
| `~/.local/share/herdr-app/` | 데스크톱 앱 바이너리와 리소스를 보관합니다. |
| `~/.local/bin/herdr-app` | 앱 바이너리를 가리키는 심볼릭 링크입니다. |
| `~/.local/bin/herdr-core` | 코어 실행 파일입니다. |
| `~/.local/bin/hc` | `herdr-core`를 가리키는 심볼릭 링크입니다. |
| `~/.local/share/applications/herdr-app.desktop` | Dash 등에서 사용하는 실행 항목입니다. |
| `~/.config/herdr-app/settings.json` | 앱 설정과 통계 전송 여부를 지정합니다. |
| `~/.config/herdr-app/keys.json` | 앱 단축키를 지정합니다. |
| `~/.config/herdr-app/mods/` | 앱에 적용한 모드를 보관합니다. |

`HERDR_APP_HOME`은 앱 설정 경로를 직접 지정하고 `XDG_CONFIG_HOME`보다 우선합니다. `XDG_DATA_HOME`을 사용하는 설치에서는 앱과 실행 항목의 경로도 달라집니다. 다른 장비에서는 실제 경로부터 확인합니다. [설정 경로 설명](https://github.com/herdrdev/herdr-app/blob/v0.1.15/docs/security.md#what-stays-on-disk)

## 새 환경에서 수행할 순서

1. 이 저장소를 준비하고 저장소 루트에서 고정된 모드 원본을 내려받습니다.

   ```sh
   git submodule update --init --recursive
   git submodule status
   ```

2. Herdr 데스크톱 앱을 설치합니다. 기존 세션에서 안내했고 사용자가 설치를 완료했다고 보고한 명령은 다음과 같습니다.

   ```sh
   curl -fsSL https://releases.herdr.dev/app/install.sh | sh
   ```

   이 명령은 실행 시점의 배포 버전을 설치하며, `0.1.15`로 고정하지 않습니다. 코어가 없으면 함께 설치하고, 설치 파일 다운로드 요청에는 최초 설치·재설치 구분이 붙습니다. 재설치하면 `.desktop` 실행 항목도 다시 작성되므로 다음 단계의 설정을 재확인합니다. [설치 스크립트 근거](https://github.com/herdrdev/herdr-app/blob/v0.1.15/distribution/install.sh)

3. 실행 파일과 설치 버전을 확인합니다. 명령을 찾지 못하면 `~/.local/bin`이 `PATH`에 포함됐는지 확인하거나 절대 경로로 실행합니다.

   ```sh
   command -v herdr-app hc herdr-core
   herdr-app --version
   hc --version
   ```

4. 첫 실행 전에 [통계 전송과 업데이트 설정](configuration.md)을 적용합니다. 설치 후 앱을 처음 실행하는 단계에서도 두 설정을 적용할 수 있도록 수정할 파일을 명시했습니다.
5. 수정한 실행 항목으로 앱을 열고 원하는 경우 Dash에 고정합니다. 기존 기록에서는 실행 항목의 설정과 실행 프로세스까지 확인했으며, Dash 고정 완료 여부 자체는 별도로 확인하지 않았습니다.
6. [Tmux prefix 적용 순서](../mods/local/tmux-prefix/README.md#적용-순서)에 따라 원본 모드를 복사하고 로컬 단축키 JSON을 기존 설정에 병합합니다.
7. `herdr-app status`의 `errors`, 설정 오류 파일, 실제 키 동작을 확인하고 날짜별 작업 기록을 남깁니다.

## 같은 버전을 재현할 때

모드 원본은 submodule 커밋으로 고정되어 있습니다. 앱과 코어의 설치 패키지 및 당시 배포 manifest는 이 저장소에 보관하지 않았으므로, 위 설치 명령만으로 동일한 바이너리를 복원할 수 있다고 보장하지 않습니다. 정확한 버전이 필요하면 해당 릴리스의 패키지와 검증 정보를 확보한 뒤 설치해야 합니다.

현재 설치 파일의 SHA-256은 [작업 기록](history/2026-11-13.md#설치-파일-식별값)에 있습니다. 이는 현재 파일을 비교하기 위한 값이며, 배포 패키지의 체크섬이나 서명 검증 결과는 아닙니다. 다른 버전을 설치하면 통계·업데이트 처리와 키 바인딩 호환성을 다시 확인합니다.

## 설치 중 겪은 문제

- 초기 세션에서는 `127.0.0.1:9010` 프록시 연결 실패로 다운로드하지 못했습니다. 프록시를 제외한 시도에서는 DNS 조회도 실패했습니다. 실행 환경의 네트워크 접근을 확인해야 하며, Herdr 설치 파일의 문제로 단정하지 않습니다.
- 당시 샌드박스에서 사용자 홈의 설치 경로와 `.git`이 읽기 전용이었고, 외부 실행 요청도 일부 거부됐습니다. 이후 권한 조건이 바뀐 세션에서 submodule 등록에 성공했습니다. 파일 소유권을 무조건 바꾸는 해결책은 적용하지 않았습니다.
- 샌드박스의 프로세스 목록에 앱이 나타나지 않아 실행 여부를 잘못 판단한 적이 있습니다. `herdr-app status` 응답과 실제 실행 환경을 함께 확인합니다.
