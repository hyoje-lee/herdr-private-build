# Tmux prefix

원본은 [herdrdev/herdr-layout-examples](https://github.com/herdrdev/herdr-layout-examples)의 [설정 안내](../../sources/herdr-layout-examples/tmux-prefix/RECIPE.md)와 [모드 폴더](../../sources/herdr-layout-examples/tmux-prefix/mods/tmux-prefix/)입니다. 직접 관리하는 단축키는 [keys.json](keys.json)에 있습니다.

`Ctrl+B` 다음 키를 Herdr 명령에 직접 연결합니다. `Ctrl+B`만 눌렀을 때에는 모드를 열지 않고, `Ctrl+B` 다음 `?`를 눌렀을 때 원본 모드의 안내 패널을 엽니다. JSON의 `ctrl-b c`처럼 공백으로 구분한 표기는 순서대로 누르는 키입니다.

| Ctrl+B 다음 키 | 동작 |
| --- | --- |
| `c` | 새 탭을 만듭니다. |
| `%` / `"` | 오른쪽 / 아래쪽으로 분할합니다. |
| `x` | 현재 pane을 닫습니다. |
| `n` / `p` | 다음 / 이전 탭으로 이동합니다. |
| `1`–`9`, `0` | 1–9번째, 10번째 탭을 선택합니다. |
| `h j k l` 또는 방향키 | 해당 방향의 pane으로 이동합니다. |
| `J` / `K` | 다음 / 이전 space로 이동합니다. |
| `z` | 현재 pane의 확대 상태를 전환합니다. |
| `d` | 앱 창을 최소화합니다. |
| `?` | 원본 모드의 안내 패널을 엽니다. |
| `Ctrl+B` | 터미널에 실제 Ctrl+B를 전달합니다. |
| `Esc` | 대기 중인 키 조합을 마칩니다. 열린 overlay가 있으면 함께 닫습니다. |

`global`과 `terminal`에는 같은 단축키를 유지합니다. `mod:tmux-prefix`의 `ctrl-b`는 안내 패널 안에서 실제 접두키를 터미널에 전달하기 위한 바인딩입니다.

직접 바인딩은 동작마다 `Ctrl+B`를 다시 눌러야 합니다. 원본 모드의 500ms 반복 입력은 안내 패널 안에서만 동작합니다. 안내 패널은 원본에 정의된 키를 표시하므로 로컬 키를 바꾸면 안내 내용도 함께 검토해야 합니다. `d`는 tmux의 detach가 아니라 앱 창 최소화입니다.

## 적용 순서

아래 명령은 저장소 루트에서 실행합니다.

1. `git submodule update --init --recursive`로 원본을 준비합니다.
2. `mods/sources/herdr-layout-examples/tmux-prefix/mods/tmux-prefix/`의 모드 파일을 검토합니다. 이 모드는 실제 키를 터미널에 전달할 때 `hc`를 실행합니다.
3. 기존 `~/.config/herdr-app/keys.json`을 백업합니다. 앱을 아직 실행하지 않은 장비에는 이 파일이 없을 수 있으며, 그때는 5단계에서 로컬 파일을 그대로 복사합니다. 앱에 `mods/tmux-prefix/`가 이미 있으면 원본과 비교하고 덮어쓰지 않습니다. 비교할 때 앱이 자동으로 만드는 `gpui-kit.d.ts`와 `jsconfig.json`은 원본에 없으므로 차이에서 제외합니다.

   ```sh
   diff -r mods/sources/herdr-layout-examples/tmux-prefix/mods/tmux-prefix \
     ~/.config/herdr-app/mods/tmux-prefix -x gpui-kit.d.ts -x jsconfig.json
   ```

4. 앱에 모드가 없으면 원본 모드 폴더를 복사합니다. `RECIPE.md`와 미리보기 이미지는 복사할 필요가 없습니다.

   ```sh
   mkdir -p ~/.config/herdr-app/mods
   cp -r mods/sources/herdr-layout-examples/tmux-prefix/mods/tmux-prefix ~/.config/herdr-app/mods/
   ```

5. `mods/local/tmux-prefix/keys.json`을 앱의 `keys.json`에 **섹션과 키별로 병합**합니다. 원본의 `tmux-prefix/keys.json`은 병합하지 않습니다. 원본 설정은 Ctrl+B를 누를 때마다 패널을 열기 때문입니다. 앱은 `keys.json`을 주석 없는 JSON으로 읽으므로 `jq`로 병합할 수 있습니다. `jq`의 `*` 병합은 같은 섹션의 같은 키를 로컬 값으로 바꾸므로, 먼저 바뀔 키를 확인합니다. 출력이 있으면 해당 키의 기존 용도를 확인한 뒤 진행합니다.

   ```sh
   keys=~/.config/herdr-app/keys.json
   local_keys=mods/local/tmux-prefix/keys.json
   if [ -f "$keys" ]; then
     # 기존 값과 다르게 바뀔 키를 출력합니다.
     jq -r -s '.[1] as $new | .[0] | to_entries[] | .key as $s | .value | to_entries[]
       | .key as $k | select($new[$s][$k]? and $new[$s][$k] != .value) | "\($s): \($k)"' \
       "$keys" "$local_keys"
     tmp=$(mktemp) && jq -s '.[0] * .[1]' "$keys" "$local_keys" > "$tmp" && mv "$tmp" "$keys"
   else
     mkdir -p ~/.config/herdr-app && cp "$local_keys" "$keys"
   fi
   ```

6. `mod:tmux-prefix` 밖에 단독 `ctrl-b` 바인딩이 남아 있으면 충돌을 해결합니다. 키 이름이 달라 5단계의 병합으로는 지워지지 않습니다. 원본 모드를 여는 바인딩은 제거하고, 다른 용도로 쓰는 바인딩은 사용자와 조정합니다.

   ```sh
   jq -r 'to_entries[] | select(.key != "mod:tmux-prefix") | .key as $s | .value | to_entries[]
     | select(.key == "ctrl-b") | "\($s): \(.value)"' ~/.config/herdr-app/keys.json
   ```
7. `herdr-app check ~/.config/herdr-app/mods/tmux-prefix`를 실행합니다. 설정 파일은 자동으로 다시 로드됩니다. `herdr-app status`의 `errors`가 비어 있는지 확인합니다. 앱은 설정을 읽지 못하면 앱 홈에 `keys.error`나 `settings.error` 파일을 만들고, 정상적으로 읽으면 지웁니다. `ls ~/.config/herdr-app/*.error`로 오류 파일이 없는지 확인한 뒤 실제 키 입력도 검증합니다.

확인할 동작은 패널 없는 접두키 대기, 새 탭과 분할, `Ctrl+B ?`의 안내 패널, `Ctrl+B Ctrl+B`의 실제 키 전달, `Esc` 취소, 일반 문자 입력입니다. `herdr-app check`는 모드의 초기 로드만 검사하므로 단축키 동작 검증을 대신하지 않습니다.

## 원본 갱신

`git -C mods/sources/herdr-layout-examples fetch origin`으로 변경을 가져온 뒤 `git -C mods/sources/herdr-layout-examples diff HEAD..origin/main -- tmux-prefix`로 영향을 확인합니다. 사용할 커밋을 선택해 submodule을 갱신하고, 로컬 JSON과 안내 패널을 함께 검증한 뒤 부모 저장소에 변경된 submodule 커밋을 기록합니다.
