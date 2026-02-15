# Plan: GitHub 신규 Repo 등록 (Public)

## Context

`aigenflow` 프로젝트 폴더를 GitHub **Public** repository로 등록합니다.
현재 git 미초기화 상태이며, `.gitignore`는 적절히 구성되어 있고 민감 파일 없음이 확인되었습니다.

## 실행 단계

### Step 1: gh CLI 설치

```bash
winget install GitHub.cli
```

- 설치 후 셸 재시작 또는 PATH 갱신 필요할 수 있음

### Step 2: gh 인증

```bash
gh auth login
```

- 이미 인증되어 있으면 스킵

### Step 3: Git 초기화 + 첫 커밋

```bash
git init
git add .
git commit -m "Initial commit"
```

### Step 4: GitHub Public Repo 생성 + Push

```bash
gh repo create aigenflow --public --source=. --push
```

## 검증

- `git log` - 커밋 확인
- `git remote -v` - 원격 저장소 연결 확인
- `gh repo view --web` - 브라우저에서 repo 확인
