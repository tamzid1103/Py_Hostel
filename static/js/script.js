// Hamburger Menu Toggle
document.addEventListener('DOMContentLoaded', function () {
    const hamburger = document.getElementById('hamburger');
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    const closeSidebar = document.getElementById('closeSidebar');
    const sidebarLinks = sidebar.querySelectorAll('a');

    if (hamburger && window.innerWidth > 768) {
        hamburger.classList.add('active');
    }

    if (hamburger) {
        hamburger.addEventListener('click', function () {
            if (window.innerWidth > 768) {
                sidebar.classList.toggle('collapsed');
                document.querySelector('.main-content').classList.toggle('expanded');
                if (sidebar.classList.contains('collapsed')) {
                    hamburger.classList.remove('active');
                } else {
                    hamburger.classList.add('active');
                }
            } else {
                hamburger.classList.toggle('active');
                sidebar.classList.toggle('active');
                sidebarOverlay.classList.toggle('active');
            }
            updateBodyScroll();
        });
    }

    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', function () {
            hamburger.classList.remove('active');
            sidebar.classList.remove('active');
            sidebarOverlay.classList.remove('active');
        });
    }

    if (closeSidebar) {
        closeSidebar.addEventListener('click', function () {
            hamburger.classList.remove('active');
            sidebar.classList.remove('active');
            sidebarOverlay.classList.remove('active');
        });
    }

    sidebarLinks.forEach(link => {
        link.addEventListener('click', function () {
            if (window.innerWidth <= 768) {
                hamburger.classList.remove('active');
                sidebar.classList.remove('active');
                sidebarOverlay.classList.remove('active');
            }
        });
    });

    window.addEventListener('resize', function () {
        if (window.innerWidth > 768) {
            sidebar.classList.remove('active');
            sidebarOverlay.classList.remove('active');
            if (!sidebar.classList.contains('collapsed')) {
                hamburger.classList.add('active');
            } else {
                hamburger.classList.remove('active');
            }
        } else {
            if (!sidebar.classList.contains('active')) {
                hamburger.classList.remove('active');
            } else {
                hamburger.classList.add('active');
            }
        }
        updateBodyScroll();
    });

    const originalOverflow = document.body.style.overflow;
    function updateBodyScroll() {
        if (sidebar && sidebar.classList.contains('active') && window.innerWidth <= 768) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = originalOverflow || 'auto';
        }
    }
});
