# Config Management - Admin Guide

## 🎯 Overview

This guide explains how to manage configuration files through Telegram bot commands.
**No SSH access or server restart required!**

## 📋 Prerequisites

1. **Admin Access**: Your Telegram user ID must be in `ADMIN_USER_IDS`
2. **Telegram Bot**: Bot must be running and accessible
3. **File Editor**: Text editor to edit YAML files locally

## 🚀 Quick Start

### Step 1: Get Your User ID

```
You: /whoami
Bot: 👤 Your Telegram Profile:
     🆔 User ID: 123456789
     👨 First name: John
     🔑 Username: @johndoe
```

Share this ID with the system administrator to get admin access.

### Step 2: Verify Access

```
You: /list_configs
Bot: 📁 Available Configuration Files:
     ✅ fees.yml - Country fees and freight costs
     ✅ commissions.yml - Company and bank commissions
     ✅ rates.yml - Exchange rates and utilization
     ✅ duties.yml - Duty calculation tables
```

If you see "🚫 Access Denied", contact your administrator.

## 📥 Downloading Configs

Download any config file to your device:

```
You: /get_fees
Bot: [sends fees.yml file]
     📄 fees.yml
     📝 Тарифы стран и фрахта
     📊 Size: 1,234 bytes
```

**Available commands:**
- `/get_fees` - Country fees and freight
- `/get_commissions` - Commissions (including bank_commission)
- `/get_rates` - Exchange rates and utilization
- `/get_duties` - Duty tables

## 📤 Uploading Configs

### Workflow

1. **Download current config** (optional, but recommended)
2. **Edit locally** on your device
3. **Validate YAML syntax** (use online validator)
4. **Upload new version**
5. **Check diff**
6. **Reload configs**

### Example: Update Fees

```
# Step 1: Download
You: /get_fees
Bot: [sends fees.yml]

# Edit locally...

# Step 2: Start upload
You: /set_fees
Bot: 📤 Upload new fees.yml
     ⚠️ File will be validated before saving.
     📏 Max size: 1MB
     
     Cancel anytime: /cancel

# Step 3: Send file
You: [upload fees.yml]
Bot: ⏳ Downloading and validating...
Bot: ✅ fees.yml updated successfully!
     📦 Backup: fees.yml.backup.20251228_153000
     ⚠️ Use /reload_configs to apply changes.

# Step 4: Check diff
You: /config_diff
Bot: 🔄 Config Diff Check
     💾 Memory hash: abc123
     💿 Disk hash: def456
     ⚠️ Out of sync - Use /reload_configs

# Step 5: Apply changes
You: /reload_configs
Bot: ⏳ Reloading configs...
Bot: ✅ Configs reloaded successfully!
     🔑 New hash: def456
     ⚡ Load time: 45ms
     🔄 Changed: Yes
```

## 🔄 Hot Reload

After uploading a new config, you must reload to apply changes:

```
You: /reload_configs
Bot: ✅ Configs reloaded successfully!
```

**No server restart needed!** All API endpoints will use new configs immediately.

## 📊 Monitoring

### Check Current Status

```
You: /config_status
Bot: 📊 Configuration Status
     🔑 Config hash: abc123def456
     📅 Loaded at: 2025-12-28 15:30:00
     📦 Total size: 12,345 bytes
     
     Files:
     ✅ fees.yml - 3,456 bytes
     ✅ commissions.yml - 2,345 bytes
     ✅ rates.yml - 1,234 bytes
     ✅ duties.yml - 5,310 bytes
```

### Check Sync Status

```
You: /config_diff
Bot: 🔄 Config Diff Check
     💾 Memory hash: abc123
     💿 Disk hash: abc123
     ✅ Up to date - Memory and disk are synchronized
```

## ⚠️ Common Issues

### Issue: Access Denied

**Problem:** You see "🚫 Access Denied"

**Solution:**
1. Get your user ID: `/whoami`
2. Contact system administrator
3. Ask to add your ID to `ADMIN_USER_IDS`
4. Wait for bot restart

### Issue: Validation Failed

**Problem:** "❌ Validation failed: Invalid YAML syntax"

**Solution:**
1. Check YAML syntax (use online validator like yamllint.com)
2. Ensure proper indentation (2 spaces, no tabs)
3. Ensure correct filename
4. Check file size (< 1MB)

### Issue: Config Not Applied

**Problem:** Changes not visible in calculations

**Solution:**
1. Check diff: `/config_diff`
2. If out of sync, reload: `/reload_configs`
3. Verify: `/config_status`

### Issue: Wrong Filename

**Problem:** "❌ Incorrect filename. Expected fees.yml, got fees_new.yml"

**Solution:**
- File must be named **exactly** as expected (e.g., `fees.yml`, not `fees_new.yml` or `fees (1).yml`)
- Don't rename files after download
- If editing, save with the exact same name

## 🛡️ Best Practices

### ✅ DO

- **Always download before editing** to get latest version
- **Validate YAML syntax** before uploading
- **Create manual backup** before major changes
- **Test in staging** environment first (if available)
- **Reload immediately** after upload
- **Monitor logs** for errors
- **Document your changes** (keep notes of what you changed)

### ❌ DON'T

- **Don't upload untested configs** - use validator first
- **Don't skip reload** - changes won't apply
- **Don't delete required keys** - validation will fail
- **Don't upload wrong filename** - must match exactly
- **Don't upload large files** - 1MB limit
- **Don't make changes during peak hours** - plan maintenance windows

## 📝 Config File Reference

### fees.yml
```yaml
countries:
  japan: 1000      # Customs clearance fee for Japan
  korea: 800       # Customs clearance fee for Korea
  # Add more countries as needed

freight:
  japan: 500       # Freight cost from Japan
  korea: 400       # Freight cost from Korea
  # Add more countries as needed
```

**What to change:**
- Update fees when customs offices change their rates
- Add new countries with their respective fees

### commissions.yml
```yaml
company_commission: 1000  # Fixed USD commission

bank_commission:
  enabled: true           # Enable/disable bank commission
  percent: 2.0            # Bank commission percentage
  min_threshold: 0        # Minimum amount for commission
  # Additional bank commission settings
```

**What to change:**
- Adjust `company_commission` for company policy changes
- Modify `bank_commission.percent` when bank rates change
- Toggle `bank_commission.enabled` to enable/disable feature

### rates.yml
```yaml
rates:
  USD: 95.0              # USD/RUB exchange rate
  EUR: 105.0             # EUR/RUB exchange rate
  CNY: 13.0              # CNY/RUB exchange rate
  # Add more currencies as needed

utilization: 5200        # Base utilization fee (RUB)
```

**What to change:**
- Update exchange rates daily (or use CBR API for automatic updates)
- Adjust `utilization` fee when government changes the rate

### duties.yml
```yaml
petrol:
  young: 0.54            # Duty rate for young petrol cars (<3 years)
  old: 3.0               # Duty rate for old petrol cars (≥3 years)

diesel:
  young: 0.54            # Duty rate for young diesel cars
  old: 3.0               # Duty rate for old diesel cars

electric:
  young: 0.15            # Duty rate for young electric cars
  old: 0.15              # Duty rate for old electric cars

hybrid:
  young: 0.54            # Duty rate for young hybrid cars
  old: 3.0               # Duty rate for old hybrid cars
```

**What to change:**
- Update duty rates when customs regulations change
- These rates are typically set by government and change infrequently

## 🔐 Security Notes

- Never share your admin credentials
- Never share `BOT_TOKEN` with unauthorized users
- Keep track of who has admin access
- Review audit logs regularly
- Report suspicious activity immediately

## 📞 Emergency Contacts

If something goes wrong:

1. **Check bot logs** (ask DevOps)
2. **Contact system administrator**
3. **Rollback**: Previous versions saved as `.backup.*` files

**System Administrator:** [Your admin contact here]  
**DevOps Team:** [Your DevOps contact here]

## 📚 Additional Resources

- [Technical Specification](SPECIFICATION.md)
- [API Documentation](API_RESULT_FLOW.md)
- [Incident Response Playbook](CONFIG_INCIDENT_PLAYBOOK.md)
- [Config Management Technical Overview](CONFIG_MANAGEMENT.md)

## 🎓 Training Scenarios

### Scenario 1: Update Exchange Rate

```
1. /get_rates              # Download current rates
2. Edit locally: USD: 95.0 → USD: 96.5
3. Validate YAML syntax
4. /set_rates              # Initiate upload
5. [Send file]             # Upload edited file
6. /reload_configs         # Apply changes
7. /config_status          # Verify new hash
```

### Scenario 2: Add New Country

```
1. /get_fees               # Download fees.yml
2. Add new country:
   countries:
     usa: 1200
   freight:
     usa: 600
3. Validate YAML
4. /set_fees               # Upload
5. [Send file]
6. /reload_configs         # Apply
7. Test API with new country
```

### Scenario 3: Emergency Rollback

```
# If you uploaded wrong config:
1. /get_fees               # Download current (wrong) version
2. Contact admin to restore from backup:
   - Backup files: fees.yml.backup.TIMESTAMP
3. /reload_configs         # Reload after admin restores
4. /config_status          # Verify restoration
```

## ❓ FAQ

**Q: Do I need to restart the bot after uploading?**  
A: No! Use `/reload_configs` for hot reload (zero downtime).

**Q: What happens if I upload invalid YAML?**  
A: Validation will fail and the old config will remain unchanged. You'll see an error message.

**Q: Can multiple admins upload configs simultaneously?**  
A: Technically yes, but **not recommended**. Coordinate changes to avoid conflicts.

**Q: Where are backups stored?**  
A: In the same `config/` directory with `.backup.TIMESTAMP` suffix.

**Q: How do I know which config is loaded?**  
A: Use `/config_status` to see the current config hash and load time.

**Q: Can I undo a change?**  
A: Ask DevOps to restore from backup file. Backups are created automatically before each update.

**Q: Why do I see "Out of sync"?**  
A: You uploaded a new config but haven't run `/reload_configs` yet.

**Q: How often should I update exchange rates?**  
A: Depends on your business needs. Daily is common, or enable CBR API for automatic updates.

---

**Version:** 1.0.0  
**Last Updated:** 2025-12-28  
**Maintained by:** DevOps Team

