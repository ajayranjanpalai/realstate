class Dashboard {
    constructor() {
        this.app = window.realEstateApp;
        this.init();
    }

    async init() {
        await this.loadDashboardData();
        this.loadFeaturedProperties();
    }

    async loadDashboardData() {
        try {
            // Load analysis data for stats
            const analysisResponse = await this.app.apiCall('/analysis');
            if (analysisResponse.success) {
                this.updateStats(analysisResponse.analysis);
            }

            // Load user bookings count
            const bookingsResponse = await this.app.apiCall('/bookings');
            if (bookingsResponse.success) {
                this.updateBookingsCount(bookingsResponse.bookings);
            }
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
        }
    }

    updateStats(analysis) {
        const stats = analysis.basic_stats;
        
        // Update stat cards
        const totalPropertiesEl = document.getElementById('totalProperties');
        const avgPriceEl = document.getElementById('avgPrice');
        const totalCitiesEl = document.getElementById('totalCities');

        if (totalPropertiesEl) {
            totalPropertiesEl.textContent = stats.total_properties.toLocaleString();
        }
        if (avgPriceEl) {
            avgPriceEl.textContent = this.app.formatPrice(stats.average_price);
        }
        if (totalCitiesEl) {
            totalCitiesEl.textContent = stats.cities_covered;
        }
    }

    updateBookingsCount(bookings) {
        const userBookingsEl = document.getElementById('userBookings');
        if (userBookingsEl) {
            userBookingsEl.textContent = bookings.length;
        }
    }

    async loadFeaturedProperties() {
        try {
            const response = await this.app.apiCall('/properties?limit=6');
            if (response.success) {
                this.displayFeaturedProperties(response.properties);
            }
        } catch (error) {
            console.error('Failed to load featured properties:', error);
        }
    }

    displayFeaturedProperties(properties) {
        const container = document.getElementById('featuredProperties');
        if (!container) return;

        if (properties.length === 0) {
            container.innerHTML = '<p class="text-center">No featured properties available.</p>';
            return;
        }

        function getPropertyImage(property) {
            if (!property) return '/static/images/apartment_1.jpg';
            const type = (property.Type || '').toLowerCase();
            const title = (property.Title || '').toLowerCase();
            const bhk = parseInt(property.BHK || 0);
            const propId = property.PropertyID || '';
            
            let hash = 0;
            for (let i = 0; i < propId.length; i++) {
                hash = (hash << 5) - hash + propId.charCodeAt(i);
                hash |= 0;
            }
            const altIndex = Math.abs(hash) % 2;

            if (type.includes('villa') || title.includes('house') || title.includes('villa')) {
                return altIndex === 0 ? '/static/images/villa_1.jpg' : '/static/images/villa_2.jpg';
            }
            if (bhk === 2 || bhk === 1) {
                return altIndex === 0 ? '/static/images/bhk2_1.jpg' : '/static/images/apartment_1.jpg';
            }
            return altIndex === 0 ? '/static/images/apartment_1.jpg' : '/static/images/apartment_2.jpg';
        }

        container.innerHTML = properties.slice(0, 6).map(property => `
            <div class="property-card">
                <div class="property-image" style="background-image: url('${getPropertyImage(property)}');">
                </div>
                <div class="property-content">
                    <h3 class="property-title">${property.Title}</h3>
                    <div class="property-location">
                        <i class="fas fa-map-marker-alt"></i>
                        ${property.Locality}, ${property.City}
                    </div>
                    <div class="property-details">
                        <div class="property-detail">
                            <i class="fas fa-expand-arrows-alt"></i>
                            ${this.app.formatArea(property.Area_sqft)}
                        </div>
                        <div class="property-detail">
                            <i class="fas fa-door-closed"></i>
                            ${property.BHK > 0 ? property.BHK + ' BHK' : 'Commercial'}
                        </div>
                        <div class="property-detail">
                            <i class="fas fa-building"></i>
                            ${property.Type}
                        </div>
                        <div class="property-detail">
                            <i class="fas fa-paint-brush"></i>
                            ${property.Furnishing}
                        </div>
                    </div>
                    <div class="property-price">
                        ${this.app.formatPrice(property.Price_Cr)}
                    </div>
                    <button class="btn-primary" onclick="viewProperty('${property.PropertyID}')">
                        <i class="fas fa-eye"></i> View Details
                    </button>
                </div>
            </div>
        `).join('');
    }
}

// Property viewing function
function viewProperty(propertyId) {
    sessionStorage.setItem('selectedProperty', propertyId);
    window.location.href = `/templates/property_detail.html?id=${encodeURIComponent(propertyId)}`;
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new Dashboard();
});