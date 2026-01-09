/**
 * Sidebar functionality for GIM Operations
 * Handles sidebar toggle, responsive behavior, and accessibility
 */

(function($) {
    'use strict';
    
    // Sidebar Controller
    const SidebarController = {
        
        // Configuration
        config: {
            sidebar: '#sidebar',
            content: '#content',
            toggleBtn: '#toggleSidebar',
            iconBtn: '#side-nav-bar-btn',
            navbar: '.top-navbar',
            breakpoint: 768,
            animationDuration: 300
        },
        
        // State
        state: {
            isCollapsed: false,
            isMobile: false,
            resizeTimer: null
        },
        
        // Initialize
        init: function() {
            this.cacheElements();
            this.bindEvents();
            this.setupInitialState();
            this.setupAccessibility();
        },
        
        // Cache DOM elements
        cacheElements: function() {
            this.$sidebar = $(this.config.sidebar);
            this.$content = $(this.config.content);
            this.$toggleBtn = $(this.config.toggleBtn);
            this.$iconBtn = $(this.config.iconBtn);
            this.$navbar = $(this.config.navbar);
            this.$window = $(window);
        },
        
        // Bind event listeners
        bindEvents: function() {
            // Toggle button click
            this.$toggleBtn.on('click.sidebar', $.proxy(this.toggleSidebar, this));
            
            // Window resize with debounce
            this.$window.on('resize.sidebar', $.proxy(this.handleResize, this));
            
            // Escape key to close sidebar on mobile
            $(document).on('keydown.sidebar', $.proxy(this.handleKeydown, this));
            
            // Click outside to close on mobile
            $(document).on('click.sidebar', $.proxy(this.handleOutsideClick, this));
        },
        
        // Setup initial state based on screen size
        setupInitialState: function() {
            this.updateMobileState();
            this.adjustSidebarForScreen();
        },
        
        // Setup accessibility attributes
        setupAccessibility: function() {
            this.$toggleBtn.attr({
                'aria-controls': 'sidebar',
                'aria-expanded': 'false',
                'aria-label': 'Alternar menú lateral',
                'role': 'button',
                'tabindex': '0'
            });
            
            this.$sidebar.attr({
                'role': 'navigation',
                'aria-label': 'Menú de navegación principal'
            });
        },
        
        // Toggle sidebar visibility
        toggleSidebar: function(e) {
            e.preventDefault();
            
            if (this.state.isMobile) {
                // Mobile behavior: show/hide sidebar
                if (this.$sidebar.hasClass('active')) {
                    // Hide sidebar
                    this.$sidebar.removeClass('active');
                    this.$sidebar.css('left', '-250px');
                    this.$toggleBtn.attr('aria-expanded', 'false');
                    this.$iconBtn
                        .removeClass('bi-arrow-bar-left')
                        .addClass('bi-arrow-bar-right');
                } else {
                    // Show sidebar
                    this.$sidebar.addClass('active');
                    this.$sidebar.css('left', '0');
                    this.$toggleBtn.attr('aria-expanded', 'true');
                    this.$iconBtn
                        .addClass('bi-arrow-bar-left')
                        .removeClass('bi-arrow-bar-right');
                }
            } else {
                // Desktop behavior: toggle collapsed state
                this.state.isCollapsed = !this.state.isCollapsed;
                
                // Update classes
                this.$sidebar.toggleClass('collapsed', this.state.isCollapsed);
                this.$content.toggleClass('expanded', this.state.isCollapsed);
                
                // Update icon
                this.updateToggleIcon();
                
                // Update accessibility
                this.$toggleBtn.attr('aria-expanded', !this.state.isCollapsed);
            }
            
            // Emit custom event
            this.$sidebar.trigger('sidebar:toggled', [!this.state.isCollapsed]);
        },
        
        // Update toggle button icon
        updateToggleIcon: function() {
            const isLeft = !this.state.isCollapsed;
            this.$iconBtn
                .toggleClass('bi-arrow-bar-left', isLeft)
                .toggleClass('bi-arrow-bar-right', !isLeft);
        },
        
        // Handle window resize
        handleResize: function() {
            // Debounce resize events
            clearTimeout(this.state.resizeTimer);
            this.state.resizeTimer = setTimeout($.proxy(this.handleResizeDebounced, this), 150);
        },
        
        // Debounced resize handler
        handleResizeDebounced: function() {
            const wasMobile = this.state.isMobile;
            this.updateMobileState();
            
            if (wasMobile !== this.state.isMobile) {
                this.adjustSidebarForScreen();
            }
        },
        
        // Update mobile state
        updateMobileState: function() {
            this.state.isMobile = this.$window.width() <= this.config.breakpoint;
        },
        
        // Adjust sidebar based on screen size
        adjustSidebarForScreen: function() {
            if (this.state.isMobile) {
                // Mobile setup - sidebar hidden by default
                this.$sidebar.removeClass('collapsed active hidden-mobile');
                this.$sidebar.css('left', '-250px');
                this.$content.addClass('expanded');
                this.$iconBtn
                    .removeClass('bi-arrow-bar-left')
                    .addClass('bi-arrow-bar-right');
                this.$toggleBtn.attr('aria-expanded', 'false');
            } else {
                // Desktop setup
                this.$sidebar.css('left', '0');
                this.$sidebar.removeClass('active hidden-mobile collapsed');
                this.$content.removeClass('expanded');
                this.$iconBtn
                    .addClass('bi-arrow-bar-left')
                    .removeClass('bi-arrow-bar-right');
                this.$toggleBtn.attr('aria-expanded', 'true');
                this.state.isCollapsed = false;
            }
            
            // Emit resize event
            this.$sidebar.trigger('sidebar:resized', [this.state.isMobile]);
        },
        
        // Handle keyboard events
        handleKeydown: function(e) {
            // Escape key to close sidebar on mobile
            if (e.keyCode === 27 && this.state.isMobile && this.$sidebar.hasClass('active')) {
                this.$sidebar.removeClass('active');
                this.$sidebar.css('left', '-250px');
                this.$iconBtn
                    .removeClass('bi-arrow-bar-left')
                    .addClass('bi-arrow-bar-right');
                this.$toggleBtn.attr('aria-expanded', 'false');
            }
        },
        
        // Handle clicks outside sidebar
        handleOutsideClick: function(e) {
            if (this.state.isMobile && 
                this.$sidebar.hasClass('active') && 
                !$(e.target).closest(this.config.sidebar + ', ' + this.config.toggleBtn).length) {
                this.$sidebar.removeClass('active');
                this.$sidebar.css('left', '-250px');
                this.$iconBtn
                    .removeClass('bi-arrow-bar-left')
                    .addClass('bi-arrow-bar-right');
                this.$toggleBtn.attr('aria-expanded', 'false');
            }
        },
        
        // Public method to check if sidebar is collapsed
        isCollapsed: function() {
            return this.state.isCollapsed;
        },
        
        // Public method to check if in mobile mode
        isMobile: function() {
            return this.state.isMobile;
        },
        
        // Destroy sidebar functionality
        destroy: function() {
            // Unbind events
            this.$toggleBtn.off('click.sidebar');
            this.$window.off('resize.sidebar');
            $(document).off('keydown.sidebar');
            $(document).off('click.sidebar');
            
            // Remove classes
            this.$sidebar.removeClass('collapsed active hidden-mobile');
            this.$content.removeClass('expanded');
            
            // Remove accessibility attributes
            this.$toggleBtn.removeAttr('aria-controls aria-expanded aria-label role tabindex');
            this.$sidebar.removeAttr('role aria-label');
        }
    };
    
    // Initialize when DOM is ready
    $(document).ready(function() {
        SidebarController.init();
        
        // Make available globally for external use
        window.GIMSidebar = SidebarController;
    });
    
})(jQuery);