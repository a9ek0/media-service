console.log('script loaded');

const API_BASE = '/api';
const POSTS_PER_PAGE = 9;

class MediaService {
    constructor() {
        console.log('constructor called');
        this.currentPage = 'index';
        this.currentCategory = 'all';
        this.currentPostsPage = 1;
        this.totalPages = 1;
        this.postsData = null;
        this.categoriesData = null;
        this.featuredPost = null;

        this.appElement = document.getElementById('app');
        if (!this.appElement) {
            console.error('Element with id "app" not found!');
            return;
        }

        this.init();
    }

    init() {
        console.log('init started');
        this.setupEventListeners();
        this.loadPage('index');
        this.setCurrentYear();
        console.log('init completed');
    }

    setupEventListeners() {
        console.log('Setting up event listeners');

        // Home link
        const homeLink = document.getElementById('home-link');
        if (homeLink) {
            homeLink.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('Home link clicked');
                this.resetFilters();
                this.loadPage('index');
            });
        } else {
            console.warn('Home link not found');
        }

        console.log('Event listeners setup completed');
    }

    setCurrentYear() {
        const yearElement = document.getElementById('current-year');
        if (yearElement) {
            yearElement.textContent = new Date().getFullYear();
        } else {
            console.warn('Year element not found');
        }
    }

    resetFilters() {
        this.currentCategory = 'all';
        this.currentPostsPage = 1;
        this.featuredPost = null;
    }

    async loadPage(pageName) {
        console.log('Loading page:', pageName);
        this.currentPage = pageName;

        try {
            this.showLoading();

            if (pageName === 'index') {
                await this.renderIndex();
            }

            console.log('Page loaded successfully:', pageName);
        } catch (error) {
            console.error('Error loading page:', error);
            this.showError('Ошибка загрузки страницы: ' + error.message);
        }
    }

    async renderIndex() {
        console.log('Rendering index page');
        try {
            if (!this.categoriesData) {
                this.categoriesData = await this.fetchCategories();
            }
            const categories = this.categoriesData.results || [];

            if (!this.featuredPost || this.currentCategory !== 'all') {
                const featuredData = await this.fetchFeaturedPost();
                this.featuredPost = featuredData.results?.[0] || null;
            }

            this.postsData = await this.fetchPosts(this.currentCategory, this.currentPostsPage);
            const posts = this.postsData.results || [];

            const totalPosts = this.postsData.count || 0;
            this.totalPages = Math.ceil(totalPosts / POSTS_PER_PAGE);

            const html = `
                ${this.featuredPost ? this.renderFeaturedPost(this.featuredPost) : ''}
                ${this.renderCategoryFilters(categories, this.currentCategory)}
                <section class="posts-grid">
                    ${posts.length > 0 
                        ? posts.map(post => this.renderPostCard(post)).join('') 
                        : '<div class="no-posts">Публикаций не найдено</div>'
                    }
                </section>
                ${this.renderPagination()}
            `;

            this.appElement.innerHTML = html;

            this.addPostEventListeners();
            this.addCategoryFilterListeners();
            this.addPaginationListeners();

        } catch (error) {
            console.error('Error rendering index:', error);
            this.showError('Ошибка загрузки страницы');
        }
    }
    async fetchFeaturedPost() {
        console.log('Fetching featured post from API');
        let url = `${API_BASE}/posts/?status=published&is_featured=true&page=1`;

        if (this.currentCategory !== 'all') {
            url += `&category__slug=${this.currentCategory}`;
        }

        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    }

    async fetchPosts(category = 'all', page = 1) {
        let url = `${API_BASE}/posts/?status=published&page=${page}`;
        if (category !== 'all') {
            url += `&category__slug=${category}`;
        }
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return response.json();
    }

    async loadPostDetail(slug) {
        try {
            console.log('Loading post detail:', slug);
            this.showLoading();

            const post = await this.fetchPost(slug);

            const html = `
                <article class="post-detail">
                    <a href="#" class="back-link" id="back-to-index">← Назад</a>
                    <h1 class="post-title">${post.title}</h1>
                    <p class="meta">
                        ${new Date(post.published_at).toLocaleString('ru-RU')} • 
                        ${post.category.name} • 
                        <span id="post-views">${post.views}</span> просмотров
                    </p>
                    ${post.cover ? `<img src="${post.cover.file}" alt="${post.cover.alt}" class="post-cover-full">` : ''}
                    <div class="post-body">${post.rendered_body}</div>
                    ${this.renderPostTags(post.tags)}
                </article>
            `;

            this.appElement.innerHTML = html;

            await this.incrementPostViews(slug);

            const updatedPost = await this.fetchPost(slug);
            const viewsElement = document.getElementById('post-views');
            if (viewsElement) {
                viewsElement.textContent = updatedPost.views;
            }

            const backButton = document.getElementById('back-to-index');
            if (backButton) {
                backButton.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.loadPage('index');
                });
            }

            console.log('Post detail loaded successfully');

        } catch (error) {
            console.error('Error loading post detail:', error);
            this.showError('Ошибка загрузки статьи: ' + error.message);
        }
    }

    async fetchPost(slug) {
        console.log('Fetching post from API:', slug);
        const response = await fetch(`${API_BASE}/posts/${slug}/`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    }

    async fetchCategories() {
        console.log('Fetching categories from API');
        const response = await fetch(`${API_BASE}/categories/`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    }

    async incrementPostViews(slug) {
        console.log('Incrementing post views:', slug);
        try {
            const response = await fetch(`${API_BASE}/posts/${slug}/hit/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            if (!response.ok) {
                console.warn('Failed to increment views:', response.status);
            } else {
                const result = await response.json();
                console.log('Views incremented:', result.views);
            }
        } catch (error) {
            console.warn('Error incrementing views:', error);
        }
    }

    getCSRFToken() {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        return cookieValue || '';
    }

    // Render methods
    renderFeaturedPost(post) {
        return `
            <section class="hero">
                <article class="hero-card">
                    <a href="#" class="post-link" data-slug="${post.slug}">
                        ${post.cover ? `<img src="${post.cover.file}" alt="${post.cover.alt}" class="hero-cover">` : ''}
                        <div class="hero-body">
                            <h1 class="hero-title">${post.title}</h1>
                            <p class="meta">${new Date(post.published_at).toLocaleString('ru-RU')} • ${post.category.name}</p>
                            <p class="excerpt">${post.excerpt}</p>
                        </div>
                    </a>
                </article>
            </section>
        `;
    }

    renderPostCard(post) {
        return `
            <article class="post-card">
                <a href="#" class="post-link" data-slug="${post.slug}">
                    ${post.cover ? `<img src="${post.cover.file}" alt="${post.cover.alt}" class="post-cover">` : ''}
                    <div class="post-body">
                        <h2 class="post-title">${post.title}</h2>
                        <p class="meta">${new Date(post.published_at).toLocaleString('ru-RU')} • ${post.category.name}</p>
                        <p class="excerpt">${post.excerpt}</p>
                    </div>
                </a>
            </article>
        `;
    }

    renderCategoryFilters(categories, currentCategory) {
        if (!categories || categories.length === 0) return '';

        return `
            <section class="filters">
                <a href="#" class="filter ${currentCategory === 'all' ? 'active' : ''}" data-category="all">Все</a>
                ${categories.map(cat => `
                    <a href="#" class="filter ${currentCategory === cat.slug ? 'active' : ''}" data-category="${cat.slug}">
                        ${cat.name}
                    </a>
                `).join('')}
            </section>
        `;
    }

    renderPagination() {
        if (this.totalPages <= 1) {
            return '';
        }

        return `
            <nav class="pagination" aria-label="Pagination">
                ${this.currentPostsPage > 1 ? 
                    `<a href="#" class="page-link" data-page="${this.currentPostsPage - 1}">← Предыдущая</a>` : 
                    '<span class="page-link disabled">← Предыдущая</span>'
                }
                
                <span class="page-info">
                    Страница ${this.currentPostsPage} из ${this.totalPages}
                </span>

                ${this.currentPostsPage < this.totalPages ? 
                    `<a href="#" class="page-link" data-page="${this.currentPostsPage + 1}">Следующая →</a>` : 
                    '<span class="page-link disabled">Следующая →</span>'
                }
            </nav>
        `;
    }

    renderPostTags(tags) {
        if (!tags || tags.length === 0) return '';
        return `
            <div class="post-tags">
                ${tags.map(tag => `<span class="tag">${tag.name}</span>`).join('')}
            </div>
        `;
    }

    addPostEventListeners() {
        document.querySelectorAll('.post-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const slug = link.dataset.slug;
                if (slug) {
                    this.loadPostDetail(slug);
                }
            });
        });
    }

    addCategoryFilterListeners() {
        document.querySelectorAll('.filter[data-category]').forEach(filter => {
            filter.addEventListener('click', (e) => {
                e.preventDefault();
                const category = filter.dataset.category;
                console.log('Category filter clicked:', category);

                this.currentCategory = category;
                this.currentPostsPage = 1;
                this.featuredPost = null;
                this.renderIndex();

                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
        });
    }

    addPaginationListeners() {
        document.querySelectorAll('.page-link[data-page]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = parseInt(link.dataset.page);
                console.log('Pagination clicked, page:', page);

                this.currentPostsPage = page;
                this.renderIndex();

                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
        });
    }

    // Helper methods
    showLoading() {
        if (this.appElement) {
            this.appElement.innerHTML = '<div id="loading">Загрузка...</div>';
        }
    }

    showError(message) {
        if (this.appElement) {
            this.appElement.innerHTML = `
                <div class="error">
                    <p>${message}</p>
                    <button onclick="location.reload()">Перезагрузить</button>
                </div>
            `;
        }
    }
}

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM fully loaded, initializing ');
    try {
        new MediaService();
        console.log('initialized successfully');
    } catch (error) {
        console.error('initialization failed:', error);
        const appElement = document.getElementById('app');
        if (appElement) {
            appElement.innerHTML = `
                <div class="error">
                    <p>Ошибка инициализации приложения</p>
                    <button onclick="location.reload()">Перезагрузить</button>
                </div>
            `;
        }
    }
});