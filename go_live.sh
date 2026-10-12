#!/usr/bin/env bash
# Flip the site from the github.io preview URL to the real domain.
# Safe to run repeatedly. Refuses to act until DNS actually points at GitHub.
set -euo pipefail

cd "$(dirname "$0")"

DOMAIN="zibaroofing.com"
REPO="gtsvenum/ziba-roofing"
GH_IPS="185.199.108.153 185.199.109.153 185.199.110.153 185.199.111.153"

echo "==> Checking DNS for $DOMAIN"
GOT=$(dig +short "$DOMAIN" A @8.8.8.8 | sort | tr '\n' ' ')
echo "    resolves to: ${GOT:-<nothing>}"

MATCHES=0
for ip in $GH_IPS; do
  case " $GOT " in *" $ip "*) MATCHES=$((MATCHES+1));; esac
done

if [ "$MATCHES" -lt 1 ]; then
  echo
  echo "STOP: $DOMAIN does not point at GitHub yet."
  echo "      Expected one or more of: $GH_IPS"
  echo "      Fix the A records at IONOS first. See DNS_SETUP.md."
  exit 1
fi
echo "    OK - $MATCHES of 4 GitHub IPs present"

echo "==> Switching generator to the live domain"
python3 - <<'PY'
import re
d = open('data.py').read()
d = re.sub(r'"pages_custom_domain": (True|False),', '"pages_custom_domain": True,', d)
d = re.sub(r'"base_path": "[^"]*",', '"base_path": "",', d)
open('data.py', 'w').write(d)
PY
grep -E '"pages_custom_domain"|"base_path"' data.py | sed 's/^/    /'

echo "==> Rebuilding"
python3 build_site.py > /dev/null
test -f site/CNAME || { echo "ERROR: CNAME not generated"; exit 1; }
echo "    CNAME = $(cat site/CNAME)"
grep -q 'href="/assets/site.css"' site/index.html \
  || { echo "ERROR: asset paths still rewritten for preview"; exit 1; }
echo "    asset paths back to root-relative"

echo "==> Committing and pushing"
git add -A
if git diff --cached --quiet; then
  echo "    nothing to commit"
else
  git -c user.name="Faraz Ardekani" -c user.email="zibamgmt@gmail.com" \
      commit -q -m "Go live on $DOMAIN"
  git push -q origin main
  echo "    pushed"
fi

echo "==> Attaching custom domain to GitHub Pages"
gh api -X PUT "repos/$REPO/pages" -f "cname=$DOMAIN" >/dev/null 2>&1 || true
sleep 3
gh api "repos/$REPO/pages" --jq '"    cname=\(.cname)  https_enforced=\(.https_enforced)"'

echo
echo "==> Waiting for the deploy to finish"
sleep 45
gh run list --limit 1 --json status,conclusion \
  --jq '"    last run: \(.[0].status) \(.[0].conclusion)"'

echo
echo "==> Live check"
for u in "http://$DOMAIN/" "http://www.$DOMAIN/"; do
  printf "    %-34s %s\n" "$u" "$(curl -sL -o /dev/null -w '%{http_code}' --max-time 20 "$u" || echo FAIL)"
done

echo
echo "Done. HTTPS certificate issues automatically within ~15 min."
echo "Then run:  gh api -X PUT repos/$REPO/pages -f https_enforced=true"
