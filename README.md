# Herdr 설치 및 설정

이 저장소는 Herdr 데스크톱 앱의 설치, 설정, 모드를 관리하는 작업 공간입니다. 다른 환경에서도 설정을 재현할 수 있도록 원본 소스, 설정 파일과 적용·검증 절차를 함께 관리합니다.

## 문서

- [문서 안내](docs/README.md): 읽는 순서와 기록 원칙을 설명합니다.
- [설치 전 확인 절차](docs/build-prerequisites.md): 코어·앱에 필요한 도구와 라이브러리를 조사하고 확인하는 방법을 설명합니다.
- [통계·업데이트 차단 빌드](docs/private-build.md): 코어·앱을 각각 별도 스크립트로 빌드·설치하는 방법을 설명합니다.
- [외부 통신 소스 검토](docs/source-audit.md): 전송 경로, 차단 정책과 SSH·모드의 신뢰 경계를 설명합니다.
- [설치와 재현](docs/setup.md): 기준 환경, 설치 경로와 재현 순서를 정리합니다.
- [통계 전송과 업데이트 설정](docs/configuration.md): 수정할 파일과 설정값, 적용 범위를 설명합니다.
- [모드 관리](mods/README.md): 외부 원본과 로컬 설정의 관리 규칙을 설명합니다.
- [Tmux prefix](mods/local/tmux-prefix/README.md): 단축키와 앱에 적용하는 방법을 설명합니다.

## 구성

```text
herdr-core/    # Herdr 코어 원본 Git submodule
herdr-app/     # Herdr 데스크톱 앱 원본 Git submodule
mods/sources/  # 외부 원본 Git submodule
mods/local/    # 직접 관리하는 설정과 수정본
scripts/       # 소스 복사·차단 패치·빌드·설치와 검사
docs/          # 설치·설정과 검증 절차
  local-history/ # Git에서 제외하는 장비별 작업 기록
AGENTS.md      # 이 작업 공간의 에이전트 작업 지침
CLAUDE.md      # AGENTS.md 참조
```

실제 앱과 개인 설정은 사용자 홈 디렉터리에 설치됩니다. 이 저장소에서는 재현에 필요한 문서, 설정 조각과 원본 소스의 고정 커밋을 관리하며, 실행 로그나 개인 상태 파일은 보관하지 않습니다. 원본을 내려받는 방법은 [설치와 재현](docs/setup.md#원본-소스)에 있습니다.
