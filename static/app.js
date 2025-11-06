const API_BASE = '/api';
let currentToken = null;
let currentUser = null;
let editingMealId = null;
let sortOrder = 'asc'; // 'asc' or 'desc'
let allMeals = []; // Store all meals for filtering
let originalMealPhoto = null; // Track original photo when editing starts
let photoRemoved = false; // Track if photo was explicitly removed

// Dark mode functions
function initDarkMode() {
    // Check for saved theme preference or default to system preference
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
        document.documentElement.setAttribute('data-theme', 'dark');
        updateDarkModeIcons(true);
    } else {
        document.documentElement.setAttribute('data-theme', 'light');
        updateDarkModeIcons(false);
    }
}

function toggleDarkMode() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateDarkModeIcons(newTheme === 'dark');
}

function updateDarkModeIcons(isDark) {
    const icon = isDark ? '☀️' : '🌙';
    const iconAuth = isDark ? '☀️' : '🌙';
    
    const darkModeIcon = document.getElementById('dark-mode-icon');
    const darkModeIconAuth = document.getElementById('dark-mode-icon-auth');
    
    if (darkModeIcon) darkModeIcon.textContent = icon;
    if (darkModeIconAuth) darkModeIconAuth.textContent = iconAuth;
}

// Check if user is already logged in
window.addEventListener('DOMContentLoaded', () => {
    initDarkMode();
    
    const token = localStorage.getItem('token');
    if (token) {
        currentToken = token;
        checkAuth();
    }
});

// Auth functions
async function checkAuth() {
    if (!currentToken) {
        console.error('No token available for auth check');
        return;
    }
    
    console.log('Checking auth with token:', currentToken.substring(0, 20) + '...');
    
    try {
        const response = await fetch(`${API_BASE}/me`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${currentToken}`,
                'Content-Type': 'application/json'
            }
        });
        
        console.log('Auth check response status:', response.status);
        
        if (response.ok) {
            currentUser = await response.json();
            console.log('Auth successful, user:', currentUser);
            showMealsView();
        } else {
            // 401 is expected if token is invalid/expired, just clear it
            if (response.status === 401) {
                const errorText = await response.text();
                console.error('Authentication failed - token invalid or expired:', errorText);
                localStorage.removeItem('token');
                currentToken = null;
            } else {
                console.error('Auth check failed with status:', response.status);
            }
        }
    } catch (error) {
        console.error('Auth check failed:', error);
        localStorage.removeItem('token');
        currentToken = null;
    }
}

function showLogin() {
    document.getElementById('login-form').classList.remove('hidden');
    document.getElementById('register-form').classList.add('hidden');
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-btn')[0].classList.add('active');
    if (document.getElementById('auth-error')) {
        document.getElementById('auth-error').textContent = '';
    }
    if (document.getElementById('register-error')) {
        document.getElementById('register-error').textContent = '';
    }
}

function showRegister() {
    document.getElementById('login-form').classList.add('hidden');
    document.getElementById('register-form').classList.remove('hidden');
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-btn')[1].classList.add('active');
    if (document.getElementById('auth-error')) {
        document.getElementById('auth-error').textContent = '';
    }
    if (document.getElementById('register-error')) {
        document.getElementById('register-error').textContent = '';
    }
}

async function login() {
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value;
    const errorDiv = document.getElementById('auth-error');
    
    if (!errorDiv) return;
    
    errorDiv.textContent = '';
    
    if (!username || !password) {
        errorDiv.textContent = 'Please fill in all fields';
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        
        if (response.ok) {
            const data = await response.json();
            currentToken = data.access_token;
            localStorage.setItem('token', currentToken);
            console.log('Login successful, token received:', currentToken.substring(0, 20) + '...');
            console.log('Token type:', typeof currentToken, 'Length:', currentToken.length);
            await checkAuth();
        } else {
            const errorData = await response.json().catch(() => ({ detail: 'Login failed' }));
            errorDiv.textContent = errorData.detail || 'Login failed';
        }
    } catch (error) {
        console.error('Login error:', error);
        errorDiv.textContent = 'Network error. Please try again.';
    }
}

async function register() {
    const username = document.getElementById('register-username').value.trim();
    const email = document.getElementById('register-email').value.trim();
    const password = document.getElementById('register-password').value;
    const errorDiv = document.getElementById('register-error') || document.getElementById('auth-error');
    
    // Clear previous errors
    if (document.getElementById('register-error')) {
        document.getElementById('register-error').textContent = '';
    }
    if (document.getElementById('auth-error')) {
        document.getElementById('auth-error').textContent = '';
    }
    
    if (!username || !email || !password) {
        if (errorDiv) errorDiv.textContent = 'Please fill in all fields';
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, email, password })
        });
        
        if (response.ok) {
            // Auto-login after registration
            const loginResponse = await fetch(`${API_BASE}/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });
            
            if (loginResponse.ok) {
                const data = await loginResponse.json();
                currentToken = data.access_token;
                localStorage.setItem('token', currentToken);
                console.log('Registration auto-login successful, token received:', currentToken.substring(0, 20) + '...');
                await checkAuth();
            } else {
                const loginError = await loginResponse.json().catch(() => ({ detail: 'Login failed' }));
                console.error('Auto-login failed:', loginError);
                if (errorDiv) errorDiv.textContent = 'Registration successful but login failed. Please login manually.';
            }
        } else {
            const errorData = await response.json().catch(() => ({ detail: 'Registration failed' }));
            if (errorDiv) errorDiv.textContent = errorData.detail || 'Registration failed';
        }
    } catch (error) {
        console.error('Registration error:', error);
        if (errorDiv) errorDiv.textContent = 'Network error. Please try again.';
    }
}

function logout() {
    currentToken = null;
    currentUser = null;
    localStorage.removeItem('token');
    document.getElementById('auth-view').classList.remove('hidden');
    document.getElementById('meals-view').classList.add('hidden');
    document.getElementById('login-username').value = '';
    document.getElementById('login-password').value = '';
    document.getElementById('register-username').value = '';
    document.getElementById('register-email').value = '';
    document.getElementById('register-password').value = '';
}

function showMealsView() {
    document.getElementById('auth-view').classList.add('hidden');
    document.getElementById('meals-view').classList.remove('hidden');
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.value = ''; // Clear search on view change
        // Ensure search input listener is set up
        if (!searchInput.hasAttribute('data-listener-attached')) {
            searchInput.addEventListener('input', () => {
                filterAndDisplayMeals();
            });
            searchInput.setAttribute('data-listener-attached', 'true');
        }
    }
    loadMeals();
}

// Meal functions
async function loadMeals() {
    try {
        const response = await fetch(`${API_BASE}/meals`, {
            headers: {
                'Authorization': `Bearer ${currentToken}`
            }
        });
        
        if (response.ok) {
            allMeals = await response.json();
            filterAndDisplayMeals();
        }
    } catch (error) {
        console.error('Failed to load meals:', error);
    }
}

function filterAndDisplayMeals() {
    const searchTerm = document.getElementById('search-input').value.trim().toLowerCase();
    
    // Filter meals based on search term
    let filteredMeals = allMeals;
    if (searchTerm) {
        filteredMeals = allMeals.filter(meal => 
            meal.name.toLowerCase().includes(searchTerm)
        );
    }
    
    displayMeals(filteredMeals);
}

function displayMeals(meals) {
    const mealsList = document.getElementById('meals-list');
    
    if (meals.length === 0) {
        mealsList.innerHTML = '<p class="empty-message">No meals yet. Click "Add Meal" to create your first one!</p>';
        return;
    }
    
    // Sort meals alphabetically
    const sortedMeals = [...meals].sort((a, b) => {
        const nameA = a.name.toLowerCase();
        const nameB = b.name.toLowerCase();
        if (sortOrder === 'asc') {
            return nameA.localeCompare(nameB);
        } else {
            return nameB.localeCompare(nameA);
        }
    });
    
    mealsList.innerHTML = sortedMeals.map(meal => {
        return `
        <div class="meal-card" onclick="showMealDetails(${meal.id})">
            <div class="meal-card-header">
                <h3>${escapeHtml(meal.name)}</h3>
                <div class="meal-menu" onclick="event.stopPropagation()">
                    <button class="meal-menu-btn" onclick="toggleMealMenu(${meal.id})">⋯</button>
                    <div id="menu-${meal.id}" class="meal-menu-dropdown hidden" onclick="event.stopPropagation()">
                        <button onclick="editMeal(${meal.id})">Edit</button>
                        <button onclick="deleteMeal(${meal.id})" class="delete-option">Delete</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    }).join('');
}

function showAddMealForm() {
    editingMealId = null;
    originalMealPhoto = null;
    photoRemoved = false;
    document.getElementById('modal-title').textContent = 'Add Meal';
    document.getElementById('meal-name').value = '';
    document.getElementById('meal-description').value = '';
    document.getElementById('meal-url').value = '';
    document.getElementById('meal-photo').value = '';
    document.getElementById('photo-preview').innerHTML = '';
    document.getElementById('remove-photo-btn').classList.add('hidden');
    document.getElementById('meal-modal').classList.remove('hidden');
}

function editMeal(mealId) {
    // Close menu and remove active class
    document.querySelectorAll('.meal-menu-dropdown').forEach(menu => {
        menu.classList.add('hidden');
        menu.closest('.meal-card')?.classList.remove('menu-active');
    });
    
    editingMealId = mealId;
    document.getElementById('modal-title').textContent = 'Edit Meal';
    
    fetch(`${API_BASE}/meals/${mealId}`, {
        headers: {
            'Authorization': `Bearer ${currentToken}`
        }
    })
    .then(response => response.json())
    .then(meal => {
        document.getElementById('meal-name').value = meal.name;
        document.getElementById('meal-description').value = meal.description || '';
        document.getElementById('meal-url').value = meal.url || '';
        document.getElementById('meal-photo').value = '';
        
        // Track original photo and show existing photo if any
        originalMealPhoto = meal.photo || null;
        photoRemoved = false;
        const photoPreview = document.getElementById('photo-preview');
        const removeBtn = document.getElementById('remove-photo-btn');
        if (meal.photo) {
            photoPreview.innerHTML = `<img src="/static/photos/${escapeHtml(meal.photo)}" alt="Meal photo" class="preview-image">`;
            removeBtn.classList.remove('hidden');
        } else {
            photoPreview.innerHTML = '';
            removeBtn.classList.add('hidden');
        }
        
        document.getElementById('meal-modal').classList.remove('hidden');
    })
    .catch(error => {
        console.error('Failed to load meal:', error);
        alert('Failed to load meal');
    });
}

function closeMealModal() {
    document.getElementById('meal-modal').classList.add('hidden');
    editingMealId = null;
    originalMealPhoto = null;
    photoRemoved = false;
    document.getElementById('meal-photo').value = '';
    document.getElementById('photo-preview').innerHTML = '';
    document.getElementById('remove-photo-btn').classList.add('hidden');
}

function removePhoto() {
    document.getElementById('meal-photo').value = '';
    document.getElementById('photo-preview').innerHTML = '';
    document.getElementById('remove-photo-btn').classList.add('hidden');
    photoRemoved = true;
}

// Preview photo when file is selected
document.addEventListener('DOMContentLoaded', () => {
    const photoInput = document.getElementById('meal-photo');
    if (photoInput) {
        photoInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                photoRemoved = false; // Reset removal flag when new file is selected
                const reader = new FileReader();
                reader.onload = (event) => {
                    const photoPreview = document.getElementById('photo-preview');
                    photoPreview.innerHTML = `<img src="${event.target.result}" alt="Preview" class="preview-image">`;
                    document.getElementById('remove-photo-btn').classList.remove('hidden');
                };
                reader.readAsDataURL(file);
            }
        });
    }
});

function toggleMealMenu(mealId) {
    // Close all other menus and remove active class from their cards
    document.querySelectorAll('.meal-menu-dropdown').forEach(menu => {
        if (menu.id !== `menu-${mealId}`) {
            menu.classList.add('hidden');
            menu.closest('.meal-card')?.classList.remove('menu-active');
        }
    });
    
    // Toggle current menu
    const menu = document.getElementById(`menu-${mealId}`);
    const isHidden = menu.classList.contains('hidden');
    menu.classList.toggle('hidden');
    
    // Add/remove active class to card for z-index management
    const card = menu.closest('.meal-card');
    if (isHidden) {
        card.classList.add('menu-active');
    } else {
        card.classList.remove('menu-active');
    }
}

function showMealDetails(mealId) {
    // Close menu and remove active class
    document.querySelectorAll('.meal-menu-dropdown').forEach(menu => {
        menu.classList.add('hidden');
        menu.closest('.meal-card')?.classList.remove('menu-active');
    });
    
    fetch(`${API_BASE}/meals/${mealId}`, {
        headers: {
            'Authorization': `Bearer ${currentToken}`
        }
    })
    .then(response => response.json())
    .then(meal => {
        const urlLink = meal.url ? `<a href="${escapeHtml(meal.url)}" target="_blank" rel="noopener noreferrer" class="detail-url">🔗 View Recipe</a>` : '<p class="no-url">No recipe URL provided</p>';
        
        // Show/hide photo section
        const photoSection = document.getElementById('detail-photo-section');
        const photoDiv = document.getElementById('detail-photo');
        if (meal.photo) {
            const photoUrl = `/static/photos/${escapeHtml(meal.photo)}`;
            photoDiv.innerHTML = `<a href="${photoUrl}" target="_blank" rel="noopener noreferrer" class="detail-photo-link"><img src="${photoUrl}" alt="${escapeHtml(meal.name)}" class="detail-photo-image"></a>`;
            photoSection.classList.remove('hidden');
        } else {
            photoSection.classList.add('hidden');
        }
        
        document.getElementById('detail-name').textContent = meal.name;
        document.getElementById('detail-description').textContent = meal.description || 'No description';
        document.getElementById('detail-url').innerHTML = urlLink;
        document.getElementById('detail-date').textContent = new Date(meal.created_at).toLocaleString();
        document.getElementById('detail-modal').classList.remove('hidden');
    })
    .catch(error => {
        console.error('Failed to load meal:', error);
        alert('Failed to load meal details');
    });
}

function closeDetailModal() {
    document.getElementById('detail-modal').classList.add('hidden');
}

async function saveMeal(event) {
    event.preventDefault();
    
    const name = document.getElementById('meal-name').value;
    const description = document.getElementById('meal-description').value;
    const mealUrl = document.getElementById('meal-url').value.trim();
    const photoFile = document.getElementById('meal-photo').files[0];
    const photoPreview = document.getElementById('photo-preview');
    
    try {
        let photoFilename = null;
        let shouldUpdatePhoto = false;
        
        // Upload photo if a new file is selected
        if (photoFile) {
            const formData = new FormData();
            formData.append('file', photoFile);
            
            const uploadResponse = await fetch(`${API_BASE}/meals/upload-photo`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${currentToken}`
                },
                body: formData
            });
            
            if (!uploadResponse.ok) {
                const error = await uploadResponse.json().catch(() => ({ detail: 'Failed to upload photo' }));
                alert(error.detail || 'Failed to upload photo');
                return;
            }
            
            const uploadData = await uploadResponse.json();
            photoFilename = uploadData.filename;
            shouldUpdatePhoto = true;
        } else if (editingMealId) {
            // When editing: check if photo was removed or keep existing
            if (photoRemoved && originalMealPhoto) {
                // Photo was explicitly removed
                photoFilename = "";
                shouldUpdatePhoto = true;
            } else if (!photoRemoved && originalMealPhoto) {
                // Keep existing photo (no changes)
                photoFilename = originalMealPhoto;
                shouldUpdatePhoto = true;
            }
            // If there was no original photo and no new file, don't update photo field
        }
        
        // Prepare meal data
        const url = editingMealId ? `${API_BASE}/meals/${editingMealId}` : `${API_BASE}/meals`;
        const method = editingMealId ? 'PUT' : 'POST';
        const body = {
            name,
            description: description || null,
            url: mealUrl || null
        };
        
        // Include photo in body if it's being set/updated
        if (shouldUpdatePhoto && photoFilename !== null) {
            body.photo = photoFilename;
        }
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentToken}`
            },
            body: JSON.stringify(body)
        });
        
        if (response.ok) {
            closeMealModal();
            loadMeals(); // Reload all meals from server
        } else {
            const error = await response.json();
            alert(error.detail || 'Failed to save meal');
        }
    } catch (error) {
        console.error('Save meal error:', error);
        alert('Network error. Please try again.');
    }
}

let pendingDeleteMealId = null;

function deleteMeal(mealId) {
    // Close menu and remove active class
    document.querySelectorAll('.meal-menu-dropdown').forEach(menu => {
        menu.classList.add('hidden');
        menu.closest('.meal-card')?.classList.remove('menu-active');
    });
    
    pendingDeleteMealId = mealId;
    document.getElementById('delete-confirm-modal').classList.remove('hidden');
}

function cancelDelete() {
    pendingDeleteMealId = null;
    document.getElementById('delete-confirm-modal').classList.add('hidden');
}

async function confirmDelete() {
    if (!pendingDeleteMealId) {
        return;
    }
    
    const mealId = pendingDeleteMealId;
    pendingDeleteMealId = null;
    document.getElementById('delete-confirm-modal').classList.add('hidden');
    
    try {
        const response = await fetch(`${API_BASE}/meals/${mealId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${currentToken}`
            }
        });
        
        if (response.ok || response.status === 204) {
            loadMeals(); // Reload all meals from server
        } else {
            const error = await response.json();
            alert(error.detail || 'Failed to delete meal');
        }
    } catch (error) {
        alert('Network error. Please try again.');
    }
}

function toggleSort() {
    sortOrder = sortOrder === 'asc' ? 'desc' : 'asc';
    const sortIcon = document.getElementById('sort-icon');
    sortIcon.textContent = sortOrder === 'asc' ? 'A-Z' : 'Z-A';
    filterAndDisplayMeals(); // Re-filter and display with new sort order
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Close modal when clicking outside
document.addEventListener('click', (e) => {
    const mealModal = document.getElementById('meal-modal');
    const detailModal = document.getElementById('detail-modal');
    const deleteModal = document.getElementById('delete-confirm-modal');
    
    if (e.target === mealModal) {
        closeMealModal();
    }
    if (e.target === detailModal) {
        closeDetailModal();
    }
    if (e.target === deleteModal) {
        cancelDelete();
    }
    
    // Close menu dropdowns when clicking outside
    if (!e.target.closest('.meal-menu')) {
        document.querySelectorAll('.meal-menu-dropdown').forEach(menu => {
            menu.classList.add('hidden');
            menu.closest('.meal-card')?.classList.remove('menu-active');
        });
    }
});

// Allow Enter key to submit login
document.getElementById('login-password').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        login();
    }
});

document.getElementById('register-password').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        register();
    }
});

