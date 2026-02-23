# DocuVerse Website - Design Specification

## Color Palette
- **Primary Green**: #22C55E (buttons, accents, leaf logo)
- **Primary Blue**: #3B82F6 (header bar, links)
- **Background Light**: #F0F9FF (light blue tint)
- **Background White**: #FFFFFF
- **Text Dark**: #1F2937 (headings)
- **Text Gray**: #6B7280 (body text)
- **Text Light**: #9CA3AF (captions)
- **Border Gray**: #E5E7EB
- **Card Background**: #FFFFFF with subtle shadow
- **Amber/Orange**: #F59E0B (accents, stars)

## Typography
- **Heading Font**: Inter or system sans-serif, bold
- **Body Font**: Inter or system sans-serif, regular
- **Hero Title**: 72px+ bold, uppercase "DOCUVERSE"
- **Section Titles**: 32-40px bold
- **Body Text**: 16px regular
- **Small Text**: 14px

## Global Animations Required
- Floating animation for hero cards (up/down 10px, 3s duration)
- Fade-in-up on scroll for sections (translateY 30px → 0, opacity 0 → 1)
- Hover lift effect on cards (translateY -8px, shadow increase)
- Button hover scale (1.02) and brightness
- Smooth scroll behavior
- Staggered animation delays for grid items (0.1s each)

## Section Breakdown

### 1. Navigation Bar
- Fixed top, blue background (#3B82F6)
- Logo: Green leaf icon + "DocuVerse" text
- Links: Home, Find Doctors, Health Overview, Emergency, AI Assistant
- Right side: Green "Book Appointment" button

### 2. Hero Section
- Light blue gradient background
- Large "DOCUVERSE" text behind doctor
- Doctor image (middle-aged, white coat, stethoscope)
- Floating health cards around doctor:
  - Heart rate: 120 bpm with heart icon
  - Blood Oxygen: 98% with icon
  - Temperature: 36.5°C with icon
  - Activity metrics
- Tagline text below
- Green CTA button "Book Appointment"

### 3. Mission Statement
- White background
- Centered text about wellness
- "Learn More" link with arrow

### 4. Your Journey to Better Care
- White background
- Left: Dr. Omar Karim profile card with image
- Middle: Search Doctor input with icon
- Right grid:
  - Emergency Services card (red/orange accent)
  - AI Overview card (green chart/graph)

### 5. Locate Trusted Experts (Specialties Grid)
- Light blue background
- 8 specialty cards in 2x4 grid:
  - Cardiology, Gastroenterology, Neurologist, Orthopedic Surgeon
  - Pulmonologist, Gynecologist, Nephrologist, Urologist
- Each card has icon, title, description

### 6. Top Doctors Section
- White background
- Left column: Section title + Award card with Dr. Omar
- Stats: "115k Trusted by Hospital"
- Three doctor profile cards with images, names, specialties
- Two feature cards: Optimize Payroll, Streamline Compliance

### 7. Key Features / App Showcase
- Light blue background
- Left: Section title + feature list
- Center: Mobile phone mockup showing app interface
- Right: "Download Now" button
- Four feature cards at bottom with icons

### 8. Testimonials
- White background
- Multiple testimonial cards with quotes
- Star ratings
- "Plus 250 Medical brunch all over the country!" banner

### 9. Contact Us
- Light gray/blue background
- Large "Contact Us" heading
- Form fields: First Name, Last Name, Services (dropdown), Email, Project description
- Office info: Manhattan, New York 2023, Office Hours
- Green Submit button

### 10. Footer
- Dark background (#1F2937)
- Four columns: About Us, Resources, Community, Legal
- Social media icons
- Copyright text

## Image Requirements
- Doctor hero image (professional, white coat)
- Dr. Omar Karim photo
- Dr. Sara Noor photo
- Dr. Amira Siddiqua photo
- Medical specialty icons (8)
- Feature icons (4)
- Mobile app mockup
- Testimonial avatars

## Tech Stack
- React + TypeScript
- Tailwind CSS
- Framer Motion for animations
- Lucide React for icons
