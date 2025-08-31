document.addEventListener('scroll', function() {
    const scrollPosition = window.scrollY;
    const sections = document.querySelectorAll('.section');
    
    sections.forEach((section, index) => {
        const sectionOffset = section.offsetTop;
        const sectionHeight = section.clientHeight;
        
        // Calculate the parallax effect
        const parallax = (scrollPosition - sectionOffset) / sectionHeight;
        section.style.transform = `translateY(${parallax * 50}px)`;
    });
});