# Secrets Management Security Documentation

## Overview

The Mycelium secrets management system provides cryptographically secure generation and storage of deployment
credentials. This document outlines security features, best practices, and considerations.

## Security Features

### 1. Cryptographically Secure Random Generation

- **Module Used**: Python's `secrets` module (not `random`)
- **Randomness Source**: OS-provided cryptographically strong random number generator
- **Password Strength**:
  - Minimum 32 characters by default
  - Guaranteed to include: lowercase, uppercase, digit, special character
  - High entropy (20+ unique characters)

### 2. Secure File Permissions

#### Secrets Files (0o600)

- **Owner**: Read and write only
- **Group**: No access
- **Others**: No access

#### Secrets Directory (0o700)

- **Owner**: Read, write, and execute
- **Group**: No access
- **Others**: No access

### 3. No Plaintext Logging

- Passwords are NEVER logged or printed in full
- Debug messages indicate password generation occurred but never reveal values
- Only password length is logged for debugging

### 4. XDG-Compliant Storage

- Secrets stored in `XDG_STATE_HOME/mycelium/secrets/`
- Default: `~/.local/state/mycelium/secrets/`
- Follows Linux/Unix standards for application state

### 5. Secret Rotation Support

- Individual secrets can be rotated without affecting others
- Old secrets are immediately replaced
- Rotation is persisted to disk automatically

## Security Best Practices

### DO

1. **Always use `.gitignore`**

   ```gitignore
   # Secrets
   .env
   .env.*
   secrets/
   *.json
   ```

1. **Use environment variables in production**

   ```python
   from mycelium_onboarding.deployment.secrets import SecretsManager

   manager = SecretsManager("production-app")
   secrets = manager.load_secrets()
   env_vars = secrets.to_env_vars()

   # Set in environment
   os.environ.update(env_vars)
   ```

1. **Rotate secrets regularly**

   ```python
   # Rotate every 90 days
   manager.rotate_secret("postgres")
   manager.rotate_secret("redis")
   manager.rotate_secret("temporal")
   ```

1. **Use separate secrets for each environment**

   ```python
   dev_manager = SecretsManager("myapp-dev")
   staging_manager = SecretsManager("myapp-staging")
   prod_manager = SecretsManager("myapp-prod")
   ```

1. **Verify file permissions after deployment**

   ```bash
   ls -la ~/.local/state/mycelium/secrets/
   # Should show: -rw------- (600)
   ```

### DON'T

1. **Never commit secrets to version control**

   - Not in code
   - Not in comments
   - Not in commit messages
   - Not in .env files

1. **Never log or print passwords**

   ```python
   # BAD
   print(f"Password: {secrets.postgres_password}")
   logger.info(f"Generated: {password}")

   # GOOD
   logger.info("Password generated successfully")
   ```

1. **Never share secrets via insecure channels**

   - No email
   - No Slack/chat (use secret sharing tools)
   - No screenshots

1. **Never use weak permissions**

   ```python
   # BAD - Don't do this
   secrets_file.chmod(0o644)  # Too permissive!

   # GOOD - System does this automatically
   secrets_file.chmod(0o600)
   ```

1. **Never reuse secrets across environments**

   ```python
   # BAD
   prod_secrets = dev_secrets  # Never!

   # GOOD
   dev_secrets = dev_manager.generate_secrets(postgres=True)
   prod_secrets = prod_manager.generate_secrets(postgres=True)
   ```

## Threat Model

### Protected Against

1. **Weak Random Number Generation**

   - Uses `secrets` module with OS entropy
   - Not predictable or reproducible

1. **Unauthorized File Access**

   - File permissions prevent other users from reading
   - Directory permissions prevent listing

1. **Information Disclosure**

   - Passwords never logged in plaintext
   - Only sanitized information in logs

1. **Password Guessing**

   - 32-character passwords with mixed character sets
   - Approximately 2^192 possible combinations

### NOT Protected Against

1. **Root/Administrator Access**

   - Root can always read files
   - Use system-level encryption for defense

1. **Memory Dumps**

   - Passwords exist in memory during use
   - Use secure memory allocation if needed

1. **Compromised Application**

   - If app is compromised, secrets may be exposed
   - Use secrets rotation and monitoring

1. **Social Engineering**

   - Humans remain weakest link
   - Use security awareness training

## Compliance Considerations

### GDPR

- Secrets are personal data if they identify users
- Implement data retention policies
- Support right to deletion (use `delete_secrets()`)

### PCI DSS

- Change default passwords immediately
- Rotate secrets quarterly
- Maintain access logs

### SOC 2

- Document secret management procedures
- Implement least privilege access
- Regular security reviews

## Production Deployment Recommendations

### 1. Use a Secrets Manager

For production systems, consider integrating with:

- **HashiCorp Vault**: Enterprise secret management
- **AWS Secrets Manager**: Cloud-native solution
- **Azure Key Vault**: Microsoft cloud solution
- **Google Secret Manager**: GCP solution

```python
# Example: Load from Vault in production, local file in development
if os.getenv("ENV") == "production":
    secrets = load_from_vault()
else:
    manager = SecretsManager("myapp-dev")
    secrets = manager.load_secrets()
```

### 2. Encrypt Secrets at Rest

```python
# Future enhancement: Add encryption layer
from cryptography.fernet import Fernet

# Encrypt before saving
encrypted_data = encrypt_with_key(secrets_data, key)
```

### 3. Audit Access

```python
# Log secret access (not values!)
logger.info(
    "Secret accessed",
    extra={
        "project": project_name,
        "secret_type": secret_type,
        "user": current_user,
        "timestamp": datetime.utcnow()
    }
)
```

### 4. Implement Secret Expiration

```python
# Future enhancement: Add expiration tracking
@dataclass
class DeploymentSecrets:
    project_name: str
    postgres_password: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None
```

## Testing Security

### Verify Randomness

```python
def test_password_uniqueness():
    """Ensure passwords are truly random."""
    manager = SecretsManager("test")
    passwords = [manager._generate_password() for _ in range(1000)]
    assert len(set(passwords)) == 1000  # All unique
```

### Verify Permissions

```python
def test_file_permissions():
    """Ensure secure file permissions."""
    import stat
    mode = secrets_file.stat().st_mode
    assert stat.S_IMODE(mode) == 0o600
```

### Verify No Logging

```python
def test_no_password_logging(caplog):
    """Ensure passwords aren't logged."""
    manager = SecretsManager("test")
    password = manager._generate_password()
    assert password not in caplog.text
```

## Incident Response

### If Secrets Are Compromised

1. **Immediately rotate all affected secrets**

   ```python
   manager.rotate_secret("postgres")
   manager.rotate_secret("redis")
   manager.rotate_secret("temporal")
   ```

1. **Update all deployments**

   - Generate new .env files
   - Restart services with new secrets
   - Verify connectivity

1. **Investigate the breach**

   - Check access logs
   - Review file permissions
   - Audit code for leaks

1. **Document and learn**

   - Post-mortem analysis
   - Update procedures
   - Additional training

## References

- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_CheatSheet.html)
- [Python secrets module documentation](https://docs.python.org/3/library/secrets.html)
- [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/)
- [CWE-798: Use of Hard-coded Credentials](https://cwe.mitre.org/data/definitions/798.html)

## Support

For security concerns or questions:

- File an issue on GitHub (do NOT include actual secrets!)
- Email: security@mycelium.dev (for responsible disclosure)
