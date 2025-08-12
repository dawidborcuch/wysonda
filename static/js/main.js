// Main JavaScript file for Wysonda

// Utility functions
function showAlert(message, type = 'info', duration = 5000) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-dismiss after specified duration
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, duration);
    }
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function generateFingerprint() {
    // Simple browser fingerprint generation
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    ctx.textBaseline = 'top';
    ctx.font = '14px Arial';
    ctx.fillText('Wysonda Fingerprint', 2, 2);
    
    const fingerprint = {
        canvas: canvas.toDataURL(),
        userAgent: navigator.userAgent,
        language: navigator.language,
        platform: navigator.platform,
        screenResolution: `${screen.width}x${screen.height}`,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        colorDepth: screen.colorDepth
    };
    
    return btoa(JSON.stringify(fingerprint));
}

function formatNumber(num) {
    return new Intl.NumberFormat('pl-PL').format(num);
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('pl-PL', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatPercentage(value, total) {
    if (total === 0) return '0%';
    return `${((value / total) * 100).toFixed(1)}%`;
}

// Local storage utilities
const Storage = {
    set: function(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (e) {
            console.error('Error saving to localStorage:', e);
            return false;
        }
    },
    
    get: function(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (e) {
            console.error('Error reading from localStorage:', e);
            return defaultValue;
        }
    },
    
    remove: function(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (e) {
            console.error('Error removing from localStorage:', e);
            return false;
        }
    },
    
    hasVoted: function(eventId) {
        const votedEvents = this.get('votedEvents', []);
        return votedEvents.includes(eventId);
    },
    
    markVoted: function(eventId) {
        const votedEvents = this.get('votedEvents', []);
        if (!votedEvents.includes(eventId)) {
            votedEvents.push(eventId);
            this.set('votedEvents', votedEvents);
        }
    }
};

// API utilities
const API = {
    baseURL: '/api',
    
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        };
        
        const finalOptions = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, finalOptions);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    },
    
    async getEvents() {
        return this.request('/events/');
    },
    
    async getEvent(eventId) {
        return this.request(`/events/${eventId}/`);
    },
    
    async getEventResults(eventId) {
        return this.request(`/events/${eventId}/results/`);
    },
    
    async vote(eventId, candidateId, fingerprint) {
        return this.request('/votes/', {
            method: 'POST',
            body: JSON.stringify({
                event_id: eventId,
                candidate_id: candidateId,
                fingerprint: fingerprint
            })
        });
    },
    
    async getStatistics() {
        return this.request('/statistics/');
    }
};

// Chart utilities (for future use)
const Charts = {
    createProgressBar(container, percentage, label) {
        const progressHtml = `
            <div class="mb-3">
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <strong>${label}</strong>
                    <span class="badge bg-primary">${percentage}%</span>
                </div>
                <div class="progress" style="height: 10px;">
                    <div class="progress-bar" role="progressbar" 
                         style="width: ${percentage}%;" 
                         aria-valuenow="${percentage}" 
                         aria-valuemin="0" aria-valuemax="100">
                    </div>
                </div>
            </div>
        `;
        container.innerHTML += progressHtml;
    },
    
    updateProgressBars(container, results) {
        container.innerHTML = '';
        results.forEach(result => {
            this.createProgressBar(container, result.percentage, result.name);
        });
    }
};

// Real-time updates
class RealTimeUpdates {
    constructor(eventId, updateInterval = 30000) {
        this.eventId = eventId;
        this.updateInterval = updateInterval;
        this.intervalId = null;
        this.isActive = false;
    }
    
    start() {
        if (this.isActive) return;
        
        this.isActive = true;
        this.intervalId = setInterval(() => {
            this.updateResults();
        }, this.updateInterval);
        
        // Initial update
        this.updateResults();
    }
    
    stop() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
        this.isActive = false;
    }
    
    async updateResults() {
        try {
            const data = await API.getEventResults(this.eventId);
            this.updateUI(data);
        } catch (error) {
            console.error('Failed to update results:', error);
        }
    }
    
    updateUI(data) {
        // Update results display
        const resultsContainer = document.getElementById('live-results');
        if (resultsContainer) {
            Charts.updateProgressBars(resultsContainer, data.results);
        }
        
        // Update total votes
        const totalVotesElement = document.querySelector('.total-votes');
        if (totalVotesElement) {
            totalVotesElement.textContent = formatNumber(data.total_votes);
        }
        
        // Update last update time
        const lastUpdateElement = document.getElementById('last-update');
        if (lastUpdateElement) {
            lastUpdateElement.textContent = new Date().toLocaleTimeString('pl-PL');
        }
        
        // Trigger custom event
        document.dispatchEvent(new CustomEvent('resultsUpdated', { detail: data }));
    }
}

// Form validation
const Validation = {
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },
    
    isValidName(name) {
        return name.trim().length >= 2;
    },
    
    isValidComment(comment) {
        return comment.trim().length >= 10 && comment.trim().length <= 1000;
    },
    
    showFieldError(field, message) {
        field.classList.add('is-invalid');
        const errorDiv = field.parentNode.querySelector('.invalid-feedback') || 
                        document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        errorDiv.textContent = message;
        
        if (!field.parentNode.querySelector('.invalid-feedback')) {
            field.parentNode.appendChild(errorDiv);
        }
    },
    
    clearFieldError(field) {
        field.classList.remove('is-invalid');
        const errorDiv = field.parentNode.querySelector('.invalid-feedback');
        if (errorDiv) {
            errorDiv.remove();
        }
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Auto-dismiss alerts
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    });
    
    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
    
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});

// Export utilities for use in other scripts
window.Wysonda = {
    showAlert,
    getCookie,
    generateFingerprint,
    formatNumber,
    formatDate,
    formatPercentage,
    Storage,
    API,
    Charts,
    RealTimeUpdates,
    Validation
};
