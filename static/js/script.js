// Hamburger Menu Toggle
document.addEventListener('DOMContentLoaded', function () {
    const hamburger = document.getElementById('hamburger');
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    const closeSidebar = document.getElementById('closeSidebar');
    const sidebarLinks = sidebar.querySelectorAll('a');
    // Toggle sidebar on hamburger click
    if (hamburger) {
        hamburger.addEventListener('click', function () {
            if (window.innerWidth > 768) {
                sidebar.classList.toggle('collapsed');
                document.querySelector('.main-content').classList.toggle('expanded');
                // also toggle active on hamburger itself for the cross animation on desktop
                hamburger.classList.toggle('active');
            } else {
                hamburger.classList.toggle('active');
                sidebar.classList.toggle('active');
                sidebarOverlay.classList.toggle('active');
            }
            updateBodyScroll();
        });
    }


    // Close sidebar on overlay click
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', function () {
            hamburger.classList.remove('active');
            sidebar.classList.remove('active');
            sidebarOverlay.classList.remove('active');
        });
    }

    // Close sidebar on close button click
    if (closeSidebar) {
        closeSidebar.addEventListener('click', function () {
            hamburger.classList.remove('active');
            sidebar.classList.remove('active');
            sidebarOverlay.classList.remove('active');
        });
    }

    // Close sidebar when a link is clicked
    sidebarLinks.forEach(link => {
        link.addEventListener('click', function () {
            // Only close on mobile/tablet
            if (window.innerWidth <= 768) {
                hamburger.classList.remove('active');
                sidebar.classList.remove('active');
                sidebarOverlay.classList.remove('active');
            }
        });
    });

    // Handle window resize - close menu on larger screens
    window.addEventListener('resize', function () {
        if (window.innerWidth > 768) {
            hamburger.classList.remove('active');
            sidebar.classList.remove('active');
            sidebarOverlay.classList.remove('active');
        }
    });

    // Prevent body scroll when sidebar is open on mobile
    const originalOverflow = document.body.style.overflow;

    function updateBodyScroll() {
        if (sidebar.classList.contains('active') && window.innerWidth <= 768) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = originalOverflow || 'auto';
        }
    }

    // Update on hamburger click
    if (hamburger) {
        hamburger.addEventListener('click', updateBodyScroll);
    }

    // Update on overlay click
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', updateBodyScroll);
    }

    // Update on close button click
    if (closeSidebar) {
        closeSidebar.addEventListener('click', updateBodyScroll);
    }

    // Update on sidebar link click
    sidebarLinks.forEach(link => {
        link.addEventListener('click', updateBodyScroll);
    });

    // Update on resize
    window.addEventListener('resize', updateBodyScroll);
});
