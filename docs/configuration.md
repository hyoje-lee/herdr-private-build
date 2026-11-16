# 통계 전송과 업데이트 설정

Herdr 데스크톱 앱 `0.1.15`를 기준으로 통계 전송과 업데이트 다운로드를 제한하는 방법을 설명합니다. 적용할 설정은 다음과 같습니다.

| 대상 | 적용값 |
| --- | --- |
| `~/.config/herdr-app/settings.json` | 최상위 `telemetry`가 `false`입니다. |
| `~/.local/share/applications/herdr-app.desktop` | `Exec`에서 `HERDR_RELEASES_URL=file:///dev/null`을 전달합니다. |

## 통계 전송 끄기

기존 `settings.json`을 백업한 뒤 최상위 객체에 다음 항목을 추가하거나 기존 값을 수정합니다. 다른 설정은 유지하고 쉼표 위치를 확인합니다.

```json
"telemetry": false
```

첫 설치로 파일이 없다면 `~/.config/herdr-app/` 디렉터리와 다음 내용의 `settings.json`을 만듭니다.

```json
{
  "telemetry": false
}
```

앱의 `Settings → Privacy`에서도 같은 설정을 바꿀 수 있습니다. 이 설정은 이후 Dash 실행에도 유지됩니다. 한 번의 실행에만 적용하려면 `DO_NOT_TRACK=1`을 사용할 수 있습니다. 통계 비활성화는 업데이트 확인이나 모드의 네트워크 요청까지 막는 설정은 아닙니다. [v0.1.15 공식 설명](https://github.com/herdrdev/herdr-app/blob/v0.1.15/docs/security.md#telemetry)

## Dash 실행 시 업데이트 다운로드 막기

기존 `.desktop` 파일을 백업한 뒤 `Exec=` 한 줄을 다음과 같이 바꿉니다. `<사용자명>`을 실제 계정 이름으로 바꾸고 실행 파일의 절대 경로를 확인합니다.

```ini
Exec=/usr/bin/env HERDR_RELEASES_URL=file:///dev/null /home/<사용자명>/.local/bin/herdr-app
```

다른 계정에서는 실행 파일의 절대 경로를 바꿉니다. `.desktop`의 `Exec`에 `~`나 `$HOME`을 그대로 넣지 않습니다. 다른 항목은 유지한 뒤 Herdr를 완전히 종료하고 해당 실행 아이콘으로 다시 엽니다.

v0.1.15의 업데이트 코드는 이 환경변수를 배포 서버 주소로 사용합니다. `file:///dev/null`을 지정하면 업데이트 정보 경로를 읽지 못하므로 새 다운로드로 진행하지 못합니다. 업데이트 기능을 끄는 공식 설정은 아니며, 검사 시도와 실패 메시지는 남을 수 있습니다. 앱의 업데이트 확인과 수동 다운로드에도 영향을 줍니다. [v0.1.15 업데이트 구현](https://github.com/herdrdev/herdr-app/blob/v0.1.15/src/update.rs)

이미 내려받아 대기 중인 업데이트까지 제거하는 방법은 아닙니다. `~/.local/share/herdr-app.new`와 `~/.local/share/herdr-app.new.json`이 있는 환경에서는 재시작 전에 대기 상태를 별도로 검토합니다.

터미널에서 `herdr-app`만 실행하면 `.desktop`의 환경변수는 적용되지 않습니다. 터미널에서도 같은 조건으로 실행하려면 다음 명령을 사용합니다.

```sh
DO_NOT_TRACK=1 HERDR_RELEASES_URL=file:///dev/null herdr-app
```

설치 스크립트를 다시 실행하면 실행 항목이 덮어써질 수 있으므로 `Exec`를 다시 확인합니다. 이 설정은 해당 앱 실행에 적용되며, 별도로 실행한 설치·업데이트 명령이나 모든 외부 통신을 차단하는 장치는 아닙니다.

## 확인과 복원

설정 변경 후 아래 명령으로 실행 항목과 앱 오류를 확인합니다. `desktop-file-validate`는 설치되어 있을 때 사용합니다.

```sh
sed -n '/^Exec=/p' ~/.local/share/applications/herdr-app.desktop
desktop-file-validate ~/.local/share/applications/herdr-app.desktop
herdr-app status
```

`settings.error`와 `keys.error`가 있는지도 확인합니다. `status`의 `errors`가 비어 있어도 실행 프로세스의 환경변수까지 검증한 것은 아닙니다. 실행 프로세스를 확인할 수 있다면 `HERDR_RELEASES_URL`만 선별해서 확인하고, 전체 환경변수는 출력하거나 기록하지 않습니다.

설정을 되돌릴 때에는 백업과 비교해 변경한 항목만 복원합니다. 업데이트 우회 설정은 `Exec`에서 환경변수 전달 부분을 제거한 뒤 앱을 다시 실행하면 해제됩니다. 통계 설정을 되돌리면 전송이 다시 활성화될 수 있으므로 원래 값과 변경 의도를 확인합니다.
