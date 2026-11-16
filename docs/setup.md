# 설치와 재현

## 기준 환경

설치·설정 절차의 기준 환경입니다. 아래 버전은 최신 버전이나 모든 환경의 호환성을 보장하는 값이 아닙니다.

| 항목 | 기준값 |
| --- | --- |
| 운영체제 | Ubuntu 24.04.4 LTS, x86_64 |
| 데스크톱 앱 | `herdr-app 0.1.15` |
| 코어 | `hc 0.1.21` (`herdr-core --version`도 같은 값을 출력합니다.) |

## 원본 소스

Herdr 코어와 앱은 작업 공간 루트에, 모드 원본은 `mods/sources/`에 Git submodule로 관리합니다.

| 경로 | 원본 저장소 |
| --- | --- |
| `herdr-core/` | <https://github.com/herdrdev/herdr-core> |
| `herdr-app/` | <https://github.com/herdrdev/herdr-app> |
| `mods/sources/herdr-layout-examples/` | <https://github.com/herdrdev/herdr-layout-examples> |

부모 저장소를 받은 뒤 `git submodule update --init --recursive`를 실행하면 부모 저장소에 고정된 커밋의 소스와 각 저장소의 하위 submodule을 내려받습니다. 이 소스는 설치된 바이너리의 버전과 별도로 관리하며, 소스를 받는 것만으로 앱이 빌드되거나 설치되지는 않습니다.

`git submodule status --recursive`로 소스 커밋과 초기화 상태를 확인합니다. 커밋 앞의 `-`는 미초기화 상태, `+`는 부모 저장소에 고정된 커밋과 다른 상태를 뜻합니다. 기존 변경이 있는 환경에서는 갱신 전에 각 submodule의 작업 트리를 확인합니다.

## 설치 경로

기본 설치 경로는 다음과 같습니다. [v0.1.15 설치 스크립트](https://github.com/herdrdev/herdr-app/blob/v0.1.15/distribution/install.sh)도 함께 참고합니다.

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

1. 이 저장소를 준비하고 저장소 루트에서 고정된 코어·앱·모드 원본을 내려받습니다.

   ```sh
   git submodule update --init --recursive
   git submodule status --recursive
   ```

2. 공식 설치 스크립트로 Herdr 데스크톱 앱을 설치합니다.

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
5. 수정한 실행 항목으로 앱을 열고 원하는 경우 Dash에 고정합니다.
6. [Tmux prefix 적용 순서](../mods/local/tmux-prefix/README.md#적용-순서)에 따라 원본 모드를 복사하고 로컬 단축키 JSON을 기존 설정에 병합합니다.
7. `herdr-app status`의 `errors`, 설정 오류 파일, 실제 키 동작을 확인합니다.

## 같은 버전을 재현할 때

코어·앱·모드의 원본 소스는 submodule 커밋으로 고정되어 있습니다. 앱과 코어의 설치 패키지 및 배포 manifest는 이 저장소에 보관하지 않으므로, 위 설치 명령만으로 동일한 바이너리를 복원할 수 있다고 보장하지 않습니다. 정확한 버전이 필요하면 해당 릴리스의 패키지와 검증 정보를 확보한 뒤 설치해야 합니다.

다른 버전을 설치하면 통계·업데이트 처리와 키 바인딩 호환성을 다시 확인합니다.

## 문제 해결

- 다운로드에 실패하면 프록시 연결, DNS와 실행 환경의 네트워크 접근을 확인합니다.
- 설치 경로나 `.git`이 읽기 전용이면 실행 환경의 쓰기 권한과 제한을 확인합니다. 파일 소유권을 일괄 변경하지 않습니다.
- 샌드박스에서는 실행 중인 앱이 프로세스 목록에 나타나지 않을 수 있습니다. `herdr-app status` 응답과 실제 실행 환경을 함께 확인합니다.
