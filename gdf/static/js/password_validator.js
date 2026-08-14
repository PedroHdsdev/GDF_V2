/**
 * Password Strength Validator
 * Validação de senha em tempo real no navegador
 * Requisitos:
 * - Mínimo 12 caracteres
 * - 1 letra maiúscula
 * - 1 letra minúscula
 * - 1 número
 * - 1 caractere especial
 */

class PasswordValidator {
    constructor(inputSelector, feedbackSelector) {
        this.input = document.querySelector(inputSelector);
        this.feedback = document.querySelector(feedbackSelector);
        this.minLength = 12;
        this.specialChars = '!@#$%^&*()_+-=[]{}|;:,.<>?';
        
        if (this.input) {
            this.input.addEventListener('input', () => this.validate());
        }
    }

    validate() {
        const password = this.input.value;
        const result = {
            length: password.length >= this.minLength,
            uppercase: /[A-Z]/.test(password),
            lowercase: /[a-z]/.test(password),
            numbers: /\d/.test(password),
            special: new RegExp(`[${this.specialChars}]`).test(password),
        };

        const strength = this.calculateStrength(password, result);
        this.updateFeedback(result, strength, password.length);
        
        return result;
    }

    calculateStrength(password, checks) {
        let strength = 0;
        
        // Comprimento
        if (password.length >= 12) strength += 10;
        if (password.length >= 16) strength += 10;
        if (password.length >= 20) strength += 20;
        
        // Variedade
        if (checks.lowercase) strength += 10;
        if (checks.uppercase) strength += 10;
        if (checks.numbers) strength += 10;
        if (checks.special) strength += 10;
        
        // Detecção de padrões
        if (!this.hasKeyboardPattern(password)) strength += 10;
        if (!this.hasSequence(password)) strength += 10;
        
        return Math.min(100, strength);
    }

    hasKeyboardPattern(password) {
        const patterns = ['qwerty', '123456', 'password', 'admin'];
        return patterns.some(p => password.toLowerCase().includes(p));
    }

    hasSequence(password) {
        return /012|123|234|345|456|567|678|789|890|abc|bcd|cde/.test(password);
    }

    static esc(s) {
        const d = document.createElement('div');
        d.textContent = s == null ? '' : String(s);
        return d.innerHTML;
    }

    updateFeedback(checks, strength, length) {
        if (!this.feedback) return;

        const requirements = [
            { met: length >= this.minLength, text: '✓ Mínimo 12 caracteres' },
            { met: checks.uppercase, text: '✓ Uma letra MAIÚSCULA' },
            { met: checks.lowercase, text: '✓ Uma letra minúscula' },
            { met: checks.numbers, text: '✓ Um número' },
            { met: checks.special, text: `✓ Um caractere especial (${this.specialChars})` },
        ];

        const unmet = requirements.filter(r => !r.met);
        const html = `
            <div class="password-strength">
                <div class="strength-meter">
                    <div class="strength-bar" style="width: ${strength}%; 
                        background-color: ${this.getStrengthColor(strength)};">
                    </div>
                </div>
                <p class="strength-text" style="color: ${this.getStrengthColor(strength)};">
                    Força: ${PasswordValidator.esc(this.getStrengthLabel(strength))}
                </p>
        `;

        if (unmet.length > 0) {
            html += '<ul class="requirements">';
            unmet.forEach(req => {
                html += '<li class="unmet">❌ ' + PasswordValidator.esc(req.text) + '</li>';
            });
            requirements.filter(r => r.met).forEach(req => {
                html += '<li class="met">' + PasswordValidator.esc(req.text) + '</li>';
            });
            html += '</ul>';
        } else {
            html += '<p style="color: green;">✅ Senha atende todos os requisitos!</p>';
        }

        html += '</div>';
        this.feedback.innerHTML = html;
    }

    getStrengthColor(strength) {
        if (strength < 40) return '#dc3545';      // Red
        if (strength < 60) return '#ffc107';      // Yellow
        if (strength < 80) return '#20c997';      // Cyan
        return '#28a745';                         // Green
    }

    getStrengthLabel(strength) {
        if (strength < 40) return 'Muito Fraca ❌';
        if (strength < 60) return 'Fraca ⚠️';
        if (strength < 80) return 'Boa ✓';
        return 'Excelente ✅';
    }

    isValid() {
        const password = this.input.value;
        const result = this.validate();
        return Object.values(result).every(v => v === true);
    }
}

// Auto-inicialize em campos com class 'password-validator'
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.password-validator').forEach(input => {
        const feedbackId = input.getAttribute('data-feedback');
        if (feedbackId) {
            new PasswordValidator(`#${input.id}`, `#${feedbackId}`);
        }
    });
});
