
document.getElementById('loginForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const loginData = {
        username: formData.get('username'),
        password: formData.get('password'),
        role: formData.get('role')
    };
    
    const messageDiv = document.getElementById('loginMessage');
    messageDiv.innerHTML = '<div class="alert alert-info">Logging in...</div>';
    
    try {
        const response = await fetch('/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(loginData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            // Store token and user info
            localStorage.setItem('authToken', result.token);
            localStorage.setItem('userInfo', JSON.stringify(result.user));
            
            // Redirect based on role
            redirectToRoleDashboard(result.user.role);
        } else {
            messageDiv.innerHTML = `<div class="alert alert-danger">${result.error}</div>`;
        }
    } catch (error) {
        messageDiv.innerHTML = `<div class="alert alert-danger">Login failed: ${error.message}</div>`;
    }
});

function redirectToRoleDashboard(role) {
    const dashboardRoutes = {
        'scientist': '/scientist-dashboard',
        'student': '/student-dashboard',
        'librarian': '/librarian-dashboard',
        'admin': '/admin-dashboard',
        'guest': '/guest-dashboard'
    };
    
    window.location.href = dashboardRoutes[role] || '/dashboard';
}

// Role selection handler
document.getElementById('role').addEventListener('change', function() {
    const role = this.value;
    const roleDescriptions = {
        'scientist': 'Full access to research documents and advanced features',
        'student': 'Access to educational materials and basic search',
        'librarian': 'Document management and user administration',
        'admin': 'Complete system administration access',
        'guest': 'Limited access to public documents'
    };
    
    // Show role description (optional)
    if (role && roleDescriptions[role]) {
        console.log(`Selected: ${roleDescriptions[role]}`);
    }
});
