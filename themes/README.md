# Herdr 테마

필요한 사람이 골라 적용할 수 있는 Herdr 앱 테마 파일을 보관합니다. 이 저장소의 설치 절차는 테마를 자동으로 적용하지 않습니다.

테마 파일은 앱이 읽는 `themes/<이름>.json` 형식을 그대로 따릅니다. 형식은 `background`, `foreground`, `selection`, `cursor`(선택), `ansi`(16색), `colors`(선택)이고 모든 색은 `#rrggbb`입니다. 패널 색은 앱이 이 값에서 계산하며, `colors`로 개별 색을 덮어쓸 수 있습니다. 자세한 규칙은 앱 홈의 `AGENTS.md`에서 `themes/<name>.json` 항목을 참고합니다.

## 테마 목록

| 테마 | 파일 | 설명 |
| --- | --- | --- |
| Ubuntu | [ubuntu.json](ubuntu.json) | Ubuntu 기본 터미널(GNOME Terminal)과 같은 색입니다. 어두운 테마입니다. |

### Ubuntu

Ubuntu 24.04의 GNOME Terminal 3.52 기본 프로필에서 색을 가져왔습니다. 이 프로필은 시스템 테마 색상을 따르므로, 배경 `#300a24`(aubergine)와 흰색 글자는 Yaru GTK 테마의 `terminal-window .terminal-screen` 규칙에서 가져왔습니다. ANSI 16색은 프로필에 저장된 GNOME 기본 팔레트입니다. GNOME Terminal에는 대응하는 값이 없어 선택 영역 색 `#5e2750`은 따로 정했습니다. 다른 Ubuntu 버전이나 다른 터미널 프로필에서는 색이 다를 수 있습니다.

## 적용 순서

아래 명령은 저장소 루트에서 실행합니다. 예시는 `ubuntu` 테마이며, 다른 테마는 파일 이름만 바꿉니다. 앱 홈은 기본적으로 `~/.config/herdr-app/`이고, `HERDR_APP_HOME`이나 `XDG_CONFIG_HOME`을 설정했다면 그 위치를 씁니다.

1. 앱 홈에 같은 이름의 테마 파일이 있는지 확인합니다. 파일이 있으면 내용을 비교하고, 직접 고친 파일이면 덮어쓰지 않습니다.

   ```sh
   diff themes/ubuntu.json ~/.config/herdr-app/themes/ubuntu.json
   ```

2. 테마 파일을 복사합니다.

   ```sh
   mkdir -p ~/.config/herdr-app/themes
   cp themes/ubuntu.json ~/.config/herdr-app/themes/
   ```

3. 테마를 선택합니다. 둘 중 하나를 고릅니다.
   - 앱의 테마 메뉴에서 `ubuntu`를 고릅니다. 이 선택은 현재 보고 있는 레이아웃에만 저장되며, 레이아웃과 `settings.json`의 테마보다 우선합니다.
   - 레이아웃에 테마가 없을 때 쓰는 기본값으로 지정하려면, `settings.json`을 백업한 뒤 `theme` 키만 병합합니다. 다른 설정은 그대로 둡니다.

     ```sh
     settings=~/.config/herdr-app/settings.json
     cp "$settings" "$settings.bak"
     tmp=$(mktemp) && jq '.theme = "ubuntu"' "$settings" > "$tmp" && mv "$tmp" "$settings"
     ```

     `settings.json`이 없으면 `{ "theme": "ubuntu" }`만 담아 새로 만듭니다. 시스템이 밝은 모드일 때 다른 테마를 쓰려면 `{"light": "paper", "dark": "ubuntu"}`처럼 지정합니다. 레이아웃이 자체 테마를 지정했거나 테마 메뉴에서 다른 테마를 고른 적이 있으면 `settings.json`의 값은 보이지 않습니다. 이때는 테마 메뉴에서 고릅니다.

4. 설정 파일은 자동으로 다시 로드됩니다. `herdr-app status`의 `errors`가 비어 있는지 확인하고, `ls ~/.config/herdr-app/*.error`로 오류 파일이 없는지 확인합니다. 그다음 화면에서 색을 확인합니다.

## 되돌리기

테마 메뉴에서 원래 테마를 고르거나, `settings.json`을 백업으로 복원합니다. 백업이 없으면 `jq 'del(.theme)'`로 `theme` 키만 지웁니다. 테마 파일을 지우기 전에 어떤 레이아웃이나 설정도 그 테마를 쓰지 않는지 확인합니다.
