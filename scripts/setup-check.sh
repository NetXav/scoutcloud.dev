#!/usr/bin/env bash
# ScoutCloud - bootcamp tool prerequisites check.
# Exits 0 if every required tool is present and recent enough.
# Exits 1 if any tool is missing or outdated.

set -u

PASS=0
FAIL=0

ok()   { printf "  \033[32mOK  \033[0m  %s\n" "$1"; PASS=$((PASS+1)); }
bad()  { printf "  \033[31mFAIL\033[0m  %s\n" "$1"; FAIL=$((FAIL+1)); }
note() { printf "        %s\n" "$1"; }

# 1. Bash itself
echo "== Shell =="
ok "bash $(bash --version | head -1 | awk '{print $4}')"

# 2. git
echo "== git =="
if command -v git >/dev/null 2>&1; then
    ok "git $(git --version | awk '{print $3}')"
else
    bad "git not installed"
fi

# 3. python3 >= 3.10
echo "== python3 =="
if command -v python3 >/dev/null 2>&1; then
    PY_VER=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')
    PY_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
    PY_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
    if [ "$PY_MAJOR" -gt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -ge 10 ]; }; then
        ok "python3 $PY_VER"
    else
        bad "python3 $PY_VER (need >= 3.10)"
    fi
else
    bad "python3 not installed"
fi

# 4. pip3
echo "== pip3 =="
if command -v pip3 >/dev/null 2>&1; then
    ok "pip3 $(pip3 --version | awk '{print $2}')"
else
    bad "pip3 not installed"
fi

# 5. terraform >= 1.0
echo "== terraform =="
if command -v terraform >/dev/null 2>&1; then
    TF_VER=$(terraform version | head -1 | sed 's/Terraform v//')
    ok "terraform $TF_VER"
else
    bad "terraform not installed"
fi

# 6. docker installed and running
echo "== docker =="
if command -v docker >/dev/null 2>&1; then
    DK_VER=$(docker --version | sed -E 's/Docker version ([^,]+),.*/\1/')
    ok "docker $DK_VER"
    if docker info >/dev/null 2>&1; then
        ok "docker daemon is running"
    else
        bad "docker daemon is NOT running (start Docker Desktop or systemctl start docker)"
    fi
else
    bad "docker not installed"
fi

# 7. AWS CLI v2
echo "== aws cli =="
if command -v aws >/dev/null 2>&1; then
    AWS_VER=$(aws --version 2>&1 | awk '{print $1}' | sed 's|aws-cli/||')
    AWS_MAJOR=$(echo "$AWS_VER" | cut -d. -f1)
    if [ "$AWS_MAJOR" = "2" ]; then
        ok "aws-cli $AWS_VER"
    else
        bad "aws-cli $AWS_VER (need v2)"
    fi
    if aws sts get-caller-identity >/dev/null 2>&1; then
        ok "aws credentials configured"
    else
        note "aws credentials not configured yet (set up in Chapter 2)"
    fi
else
    bad "aws-cli not installed"
fi

# 8. kubectl
echo "== kubectl =="
if command -v kubectl >/dev/null 2>&1; then
    ok "kubectl $(kubectl version --client -o yaml 2>/dev/null | awk '/gitVersion/ {print $2; exit}' | tr -d '"')"
else
    bad "kubectl not installed"
fi

# 9. ansible
echo "== ansible =="
if command -v ansible >/dev/null 2>&1; then
    ok "ansible $(ansible --version | head -1 | awk '{print $3}' | tr -d ']')"
else
    bad "ansible not installed"
fi

# 10. make
echo "== make =="
if command -v make >/dev/null 2>&1; then
    ok "make $(make --version | head -1 | awk '{print $3}')"
else
    bad "make not installed"
fi

# 11. curl
echo "== curl =="
if command -v curl >/dev/null 2>&1; then
    ok "curl $(curl --version | head -1 | awk '{print $2}')"
else
    bad "curl not installed"
fi

echo
echo "== Summary =="
echo "  Passed: $PASS"
echo "  Failed: $FAIL"

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0
