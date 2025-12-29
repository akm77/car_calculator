# Config Management - Incident Response Playbook

## 🚨 Critical Incidents

### INCIDENT-001: Config Reload Failed

**Severity:** P1 (High)

**Symptoms:**
- `/reload_configs` returns error
- "❌ Config reload failed" message
- Old configs remain in memory
- API calculations may be using stale data

**Diagnosis:**
```bash
# Check bot logs
docker logs car-calculator-bot | grep config_reload_failed

# Check recent config changes
docker logs car-calculator-bot | grep config_updated | tail -10

# Check config file syntax
yamllint config/*.yml

# Check file permissions
ls -la config/

# Check for partial writes or corruption
for f in config/*.yml; do echo "=== $f ==="; head -5 "$f"; done
```

**Resolution:**

**Option 1: Fix Syntax Error**
1. Identify problematic file from error message
2. SSH into server
3. Fix YAML syntax:
   ```bash
   vi config/fees.yml  # or nano, vim, etc.
   ```
4. Validate:
   ```bash
   yamllint config/fees.yml
   ```
5. Retry in Telegram: `/reload_configs`

**Option 2: Restore from Backup**
```bash
# List available backups
ls -lt config/*.backup.* | head -10

# Restore specific file (replace TIMESTAMP)
cp config/fees.yml.backup.20251228_150000 config/fees.yml

# Reload in Telegram
# Telegram: /reload_configs
```

**Option 3: Restore from Git**
```bash
# Check git status
git status config/

# Restore all configs to last commit
git checkout HEAD -- config/

# Or restore specific file
git checkout HEAD -- config/fees.yml

# Reload in Telegram
# Telegram: /reload_configs
```

**Prevention:**
- Always validate YAML before upload
- Use staging environment for testing
- Implement pre-commit hooks for YAML validation
- Set up monitoring alerts

**Escalation:** If reload still fails after fixing syntax → Escalate to P0

---

### INCIDENT-002: All Configs Lost

**Severity:** P0 (Critical)

**Symptoms:**
- Bot cannot start
- "Config files missing" error in logs
- `/get_*` commands return "File not found"
- API returns 500 errors

**Diagnosis:**
```bash
# Check if config directory exists
ls -la config/

# Check for any remaining files
find config/ -name "*.yml"

# Check for backups
ls -la config/*.backup.*

# Check disk space
df -h

# Check recent file operations in logs
docker logs car-calculator-bot | grep -i "config" | tail -50
```

**Resolution:**

**Option 1: Restore from Latest Backup**
```bash
cd config/

# Find most recent backup set (same timestamp)
LATEST_TS=$(ls *.backup.* 2>/dev/null | grep -oE '[0-9]{8}_[0-9]{6}' | sort -u | tail -1)

if [ -n "$LATEST_TS" ]; then
    echo "Restoring from backup: $LATEST_TS"
    for f in *.backup.$LATEST_TS; do
        original="${f%.backup.*}"
        cp "$f" "$original"
        echo "Restored: $original"
    done
else
    echo "No backups found!"
fi

# Verify restoration
ls -la *.yml

# Restart bot
docker restart car-calculator-bot
```

**Option 2: Restore from Git**
```bash
# Restore entire config directory
git checkout HEAD -- config/

# Or restore to specific commit
git checkout <commit-hash> -- config/

# Verify
ls -la config/*.yml

# Restart bot
docker restart car-calculator-bot
```

**Option 3: Restore from External Backup**
```bash
# If you have external backups (e.g., S3, NAS)
aws s3 sync s3://your-bucket/config-backups/latest/ config/

# Or from NAS
rsync -av /mnt/backup/car-calculator/config/ config/

# Restart bot
docker restart car-calculator-bot
```

**Prevention:**
- Daily automated backups to external storage
- Git versioning
- Implement file system monitoring
- Regular backup testing (quarterly)

**Escalation:** Notify CTO immediately → Follow disaster recovery plan

---

### INCIDENT-003: Unauthorized Access Attempt

**Severity:** P2 (Medium)

**Symptoms:**
- Logs show "unauthorized_access_attempt"
- Unknown user trying admin commands
- Multiple failed access attempts from same user
- Unusual command patterns

**Diagnosis:**
```bash
# Check logs for unauthorized attempts
docker logs car-calculator-bot | grep unauthorized_access_attempt

# Get details of suspicious users
docker logs car-calculator-bot | grep unauthorized_access_attempt | grep -oE 'user_id=[0-9]+' | sort | uniq -c

# Check recent activity from specific user (replace USER_ID)
docker logs car-calculator-bot | grep "user_id=999999"

# Check for patterns (repeated attempts)
docker logs car-calculator-bot | grep unauthorized_access_attempt | \
    awk '{print $1, $2}' | uniq -c | sort -rn
```

**Resolution:**

**Step 1: Verify if Legitimate**
1. Contact the user (check username in logs)
2. Verify if they should have access
3. If legitimate → Add to `ADMIN_USER_IDS` and restart bot

**Step 2: If Malicious**
```bash
# Option 1: Block in Telegram (if bot has admin rights in group)
# Do this through Telegram interface

# Option 2: Add rate limiting (development task)
# Create ticket for implementing rate limiting

# Option 3: If BOT_TOKEN compromised
# 1. Revoke token in @BotFather
# 2. Generate new token
# 3. Update environment variable
# 4. Restart bot
```

**Step 3: Review and Audit**
```bash
# Generate security report
docker logs car-calculator-bot | \
    grep -E "(unauthorized_access_attempt|admin_command_executed)" | \
    grep -E "$(date +%Y-%m-%d)" > /tmp/security-audit-$(date +%Y%m%d).log

# Analyze patterns
cat /tmp/security-audit-*.log | \
    grep -oE 'user_id=[0-9]+' | sort | uniq -c | sort -rn
```

**Prevention:**
- Keep `BOT_TOKEN` secret (never commit to git)
- Regular audit of admin list
- Implement rate limiting for failed attempts
- Set up alerting for suspicious patterns
- Consider 2FA for critical operations

**Escalation:** If token compromised → Escalate to P0

---

### INCIDENT-004: Config Out of Sync

**Severity:** P3 (Low)

**Symptoms:**
- `/config_diff` shows "Out of sync"
- Calculations use old values
- Admin uploaded config but forgot to reload
- Memory hash ≠ Disk hash

**Diagnosis:**
```bash
# Check via Telegram
# Telegram: /config_diff

# Check bot logs for last reload
docker logs car-calculator-bot | grep config_reload | tail -5

# Check last config update
docker logs car-calculator-bot | grep config_updated | tail -5

# Check file timestamps
ls -lt config/*.yml
```

**Resolution:**

**Simple Fix:**
```
Admin (Telegram): /reload_configs
Bot: ✅ Configs reloaded successfully!

Admin: /config_diff
Bot: ✅ Up to date
```

**If Reload Fails:**
1. Check for syntax errors (see INCIDENT-001)
2. Verify file integrity
3. Check logs for specific error
4. Follow INCIDENT-001 resolution

**Prevention:**
- Always reload immediately after upload
- Automated reminder message after upload
- Implement health check endpoint that monitors sync status
- Set up monitoring alert for out-of-sync (>30 minutes)

**Escalation:** If not resolved in 30 minutes → Escalate to P2

---

### INCIDENT-005: Config Validation Failing

**Severity:** P2 (Medium)

**Symptoms:**
- All config uploads are rejected
- "Validation failed" for known-good files
- Validation logic may be broken

**Diagnosis:**
```bash
# Test validation manually
python3 << 'EOF'
import yaml
from pathlib import Path

config_dir = Path("config")
for yml_file in config_dir.glob("*.yml"):
    try:
        with open(yml_file) as f:
            data = yaml.safe_load(f)
        print(f"✅ {yml_file.name}: OK")
    except Exception as e:
        print(f"❌ {yml_file.name}: {e}")
EOF

# Check validation code for recent changes
git log --oneline -10 app/bot/handlers/config.py
git log --oneline -10 app/core/settings.py

# Check for Python/dependency issues
docker exec car-calculator-bot python --version
docker exec car-calculator-bot pip list | grep -i yaml
```

**Resolution:**

**Option 1: Code Issue**
```bash
# Rollback to last known good version
git log --oneline app/bot/handlers/config.py
git checkout <good-commit-hash> -- app/bot/handlers/config.py

# Rebuild and restart
docker-compose build bot
docker-compose up -d bot
```

**Option 2: Dependency Issue**
```bash
# Rebuild with fresh dependencies
docker-compose build --no-cache bot
docker-compose up -d bot
```

**Option 3: Temporary Bypass (Emergency Only)**
```python
# Edit app/bot/handlers/config.py
# Comment out strict validation temporarily
# ONLY DO THIS IN EMERGENCY!

# After fixing configs, restore validation
git checkout app/bot/handlers/config.py
```

**Prevention:**
- Unit tests for validation logic
- Integration tests with various config samples
- Don't modify validation logic without thorough testing

**Escalation:** If affecting production → Escalate to P1

---

## 🔍 Diagnostic Commands

### Bot Health Check

```bash
# Is bot running?
docker ps | grep car-calculator-bot

# Bot logs (last 50 lines)
docker logs --tail 50 car-calculator-bot

# Bot logs (follow in real-time)
docker logs -f car-calculator-bot

# Filter for errors
docker logs car-calculator-bot | grep -i error | tail -20

# Filter for warnings
docker logs car-calculator-bot | grep -i warning | tail -20

# Config-related events
docker logs car-calculator-bot | grep config_ | tail -30
```

### Config Files Check

```bash
# List all configs with details
ls -lh config/*.yml

# Validate all YAML files
yamllint config/*.yml

# Check syntax of specific file
python3 -c "import yaml; yaml.safe_load(open('config/fees.yml'))" && echo "✅ OK" || echo "❌ ERROR"

# Check file sizes
du -h config/*.yml

# Count total backups
ls -1 config/*.backup.* 2>/dev/null | wc -l

# Find latest backup for each config
for cfg in fees commissions rates duties; do
    echo "=== $cfg.yml ==="
    ls -t config/${cfg}.yml.backup.* 2>/dev/null | head -1
done

# Check disk usage
df -h | grep -E '(Filesystem|/dev/)'
```

### Admin Access Check

```bash
# Get admin IDs from environment
docker exec car-calculator-bot printenv ADMIN_USER_IDS

# Or from .env file
grep ADMIN_USER_IDS .env

# Check bot startup logs for admin count
docker logs car-calculator-bot | grep "admin_count" | tail -1

# List recent admin commands
docker logs car-calculator-bot | grep admin_command_executed | tail -20
```

### Performance Check

```bash
# Config load times
docker logs car-calculator-bot | grep "load_time_ms" | tail -10

# Memory usage
docker stats car-calculator-bot --no-stream

# Container resource limits
docker inspect car-calculator-bot | grep -A 10 "Memory"
```

---

## 📊 Monitoring & Alerting

### Recommended Alerts

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| Config Reload Failed | reload fails 3+ times in 1 hour | P1 | Check logs, fix syntax |
| Unauthorized Access Spike | 10+ attempts in 1 hour | P2 | Review security logs |
| Missing Config Files | Any .yml missing | P0 | Restore from backup |
| Out of Sync | >30 minutes | P3 | Remind admin to reload |
| Large Config File | Size >500KB | P3 | Review file contents |
| Validation Failures | 5+ failures in 1 hour | P2 | Check validation logic |
| Bot Down | Container not running | P0 | Restart bot, check logs |

### Health Check Endpoint

```bash
# Check bot health (if API available)
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "config_hash": "abc123def456",
#   "loaded_at": "2025-12-28T15:30:00Z"
# }
```

---

## 🔄 Rollback Procedures

### Rollback Single Config

```bash
# Step 1: Find latest good backup
ls -lt config/fees.yml.backup.* | head -5

# Step 2: Identify timestamp of good version
# Example: fees.yml.backup.20251228_150000

# Step 3: Restore
cp config/fees.yml.backup.20251228_150000 config/fees.yml

# Step 4: Reload in Telegram
# Telegram: /reload_configs

# Step 5: Verify
# Telegram: /config_status
# Telegram: /config_diff
```

### Rollback All Configs

**Option 1: From Backups (specific timestamp)**
```bash
# Set timestamp of good backup set
GOOD_TS="20251228_150000"

cd config/
for f in *.backup.$GOOD_TS; do
    original="${f%.backup.$GOOD_TS}"
    cp "$f" "$original"
    echo "Restored: $original"
done

# Telegram: /reload_configs
```

**Option 2: From Git (specific commit)**
```bash
# View recent commits
git log --oneline -10 config/

# Restore to specific commit
git checkout <commit-hash> -- config/

# Telegram: /reload_configs
```

**Option 3: From External Backup**
```bash
# From S3
aws s3 sync s3://your-bucket/backups/20251228/ config/

# From local backup directory
rsync -av /backup/car-calculator/config_20251228/ config/

# Telegram: /reload_configs
```

---

## 📞 Escalation Matrix

| Severity | Response Time | Who to Contact | Communication Channel |
|----------|---------------|----------------|----------------------|
| **P0** (Critical) | 15 minutes | DevOps Team + CTO | Phone + Slack |
| **P1** (High) | 1 hour | DevOps Team | Slack + Email |
| **P2** (Medium) | 4 hours | DevOps Team | Slack |
| **P3** (Low) | 1 business day | System Admin | Email |

### Contact List

```
DevOps Team:
- Primary: +1-555-0100 (Slack: @devops-team)
- Secondary: +1-555-0101 (Slack: @devops-oncall)

System Admin:
- Email: admin@example.com
- Telegram: @sysadmin

CTO (P0 only):
- Phone: +1-555-0001
- Slack: @cto
```

---

## 📝 Post-Incident Checklist

After resolving an incident:

- [ ] **Document incident details**
  - What happened (root cause)
  - When it started
  - Impact (users affected, duration)
  - Resolution steps taken

- [ ] **Update runbooks**
  - Add new scenarios if not covered
  - Update resolution steps if improved
  - Add lessons learned

- [ ] **Notify stakeholders**
  - Send incident summary
  - Explain impact and resolution
  - Provide timeline

- [ ] **Create follow-up tickets**
  - Fix root cause (if not yet fixed)
  - Improve monitoring/alerting
  - Add automation to prevent recurrence

- [ ] **Schedule post-mortem** (P0/P1 only)
  - Within 48 hours of resolution
  - Include all relevant team members
  - Document findings and action items

---

## 🧪 Testing Incident Response

### Quarterly Drill Schedule

**Q1: Config Corruption Drill**
```bash
# Simulate corrupted config
echo "invalid: yaml: [[[" > config/fees.yml

# Expected:
# 1. Admin tries /reload_configs → fails
# 2. Team follows INCIDENT-001 procedure
# 3. Restore from backup
# 4. Reload succeeds
# Time limit: 15 minutes
```

**Q2: Total Loss Drill**
```bash
# Simulate total config loss (use backup location!)
mv config config_backup_drill
mkdir config

# Expected:
# 1. Bot fails to start
# 2. Team follows INCIDENT-002 procedure
# 3. Restore from git or backup
# Time limit: 30 minutes
```

**Q3: Security Incident Drill**
```bash
# Simulate unauthorized access (coordinate with team)
# Have a team member use non-admin account to try admin commands

# Expected:
# 1. Commands are blocked
# 2. Logs show unauthorized attempts
# 3. Team reviews logs and identifies user
# Time limit: 20 minutes
```

**Q4: Full Disaster Recovery Drill**
```bash
# Simulate complete system failure
# Expected:
# 1. Restore configs from external backup
# 2. Restart bot
# 3. Verify all functionality
# Time limit: 1 hour
```

---

## 📚 Additional Resources

- [Admin User Guide](CONFIG_ADMIN_GUIDE.md)
- [Technical Documentation](CONFIG_MANAGEMENT.md)
- [API Documentation](API_RESULT_FLOW.md)
- [System Architecture](SPECIFICATION.md)

---

**Playbook Version:** 1.0.0  
**Last Updated:** 2025-12-28  
**Next Review:** 2026-03-28  
**Maintained by:** DevOps Team

