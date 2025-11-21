// SEO Enhancement Script for FastAPI Ronin Documentation
document.addEventListener('DOMContentLoaded', function() {

    // Add essential structured data
    function addStructuredData() {
        const baseUrl = 'https://bubaley.github.io/fastapi-ronin';

        const websiteData = {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": "FastAPI Ronin",
            "description": "Django REST Framework-inspired ViewSets and utilities for FastAPI applications with Tortoise ORM",
            "url": baseUrl,
            "publisher": {
                "@type": "Organization",
                "name": "FastAPI Ronin",
                "url": "https://github.com/bubaley/fastapi-ronin"
            }
        };

        const softwareData = {
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            "name": "FastAPI Ronin",
            "description": "Build REST APIs fast with Django REST Framework patterns in FastAPI. ViewSets, permissions, pagination, and automatic CRUD operations.",
            "applicationCategory": "WebApplication",
            "programmingLanguage": "Python",
            "url": baseUrl,
            "downloadUrl": "https://pypi.org/project/fastapi-ronin/",
            "license": "https://github.com/bubaley/fastapi-ronin/blob/main/LICENSE",
            "keywords": ["FastAPI", "Django REST Framework", "ViewSets", "Python", "REST API", "Tortoise ORM"]
        };

        addJSONLD('website-data', websiteData);
        addJSONLD('software-data', softwareData);
    }

    function addJSONLD(id, data) {
        if (!document.getElementById(id)) {
            const script = document.createElement('script');
            script.type = 'application/ld+json';
            script.id = id;
            script.textContent = JSON.stringify(data);
            document.head.appendChild(script);
        }
    }

    function getPageDescription() {
        const metaDesc = document.querySelector('meta[name="description"]');
        if (metaDesc) return metaDesc.content;

        const firstParagraph = document.querySelector('article p, .md-content p');
        if (firstParagraph) {
            return firstParagraph.textContent.slice(0, 160) + '...';
        }

        return 'FastAPI Ronin documentation - Django REST Framework patterns for FastAPI applications.';
    }

    // Add essential social meta tags
    function addSocialMetaTags() {
        const currentUrl = window.location.href;
        const title = document.title;
        const description = getPageDescription();
        const image = 'https://bubaley.github.io/fastapi-ronin/assets/logo.png';

        const metaTags = [
            { property: 'og:type', content: 'website' },
            { property: 'og:title', content: title },
            { property: 'og:description', content: description },
            { property: 'og:url', content: currentUrl },
            { property: 'og:image', content: image },
            { property: 'og:site_name', content: 'FastAPI Ronin' },

            { name: 'twitter:card', content: 'summary' },
            { name: 'twitter:title', content: title },
            { name: 'twitter:description', content: description },
            { name: 'twitter:image', content: image },

            { name: 'robots', content: 'index, follow' }
        ];

        metaTags.forEach(tag => {
            if (!document.querySelector(`meta[${tag.property ? 'property' : 'name'}="${tag.property || tag.name}"]`)) {
                const meta = document.createElement('meta');
                if (tag.property) {
                    meta.setAttribute('property', tag.property);
                } else {
                    meta.setAttribute('name', tag.name);
                }
                meta.setAttribute('content', tag.content);
                document.head.appendChild(meta);
            }
        });

        // Add canonical URL
        if (!document.querySelector('link[rel="canonical"]')) {
            const canonical = document.createElement('link');
            canonical.rel = 'canonical';
            canonical.href = currentUrl;
            document.head.appendChild(canonical);
        }
    }

    // Add language attribute
    if (!document.documentElement.lang) {
        document.documentElement.lang = 'en';
    }

    // Initialize SEO enhancements
    addStructuredData();
    addSocialMetaTags();
});
