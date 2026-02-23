# Session Context — Action Chiropractic Website

## What This Project Is
A spec/demo website for **Action Chiropractic P.C.** — a real chiropractor's business. It's a React + Vite + Tailwind CSS + Framer Motion site located at `Chiropractic-website-number-/`. Run it with `npm run dev` from that directory; it serves on `http://localhost:5173`.

## Business Info (From the Doctor's Business Card)
- **Business:** Action Chiropractic P.C.
- **Doctor:** Dr. Bruce C. Bromberg, Chiropractor
- **Address:** 179 School Street – Unit A, Westbury, NY 11590
- **Phone:** 516-280-7470
- **Fax:** 516-280-7469
- **Cell (handwritten on card):** 516-319-9832
- **Email:** ActionChiroNow@gmail.com
- **Features:** Digital X-Ray done on site, Se habla Español

## Current State of the Build

### Hero Section (`sections/Hero.tsx`)
- **Redesigned to match a Dribbble reference** (Modern AI Healthcare UI)
- Full-viewport sky gradient background (dark blue top → white bottom)
- White cloud blur shapes with `animate-cloud-drift` animation
- Massive outlined **"ACTION CHIRO"** text behind the doctor (transparent fill, white stroke, responsive from 80px to 320px)
- **Doctor image** is a transparent PNG cutout (`/public/dr-bromberg-hero.png`) — background was removed using `rembg`. Displayed with `object-contain object-bottom`, no `mix-blend-mode`. Container: `w-[300px] h-[420px]` scaling up to `md:w-[420px] md:h-[580px]`
- Bottom gradient fade from transparent to white
- **5 floating UI cards** (absolutely positioned, `z-20`, framer-motion staggered entrance + CSS float animations):
  1. **Meet the Doctor** (far left, `left: 2%`, `top: 30%`) — Dr. Bruce C. Bromberg, Chiropractor, 30+ years
  2. **Book Appointment** (left-center, `left: 20%`, `top: 18%`) — Office hours Mon-Fri 9-6, Sat 10-2, Schedule Now button
  3. **Why Patients Trust Us** (center-right, `right: 18%`, `top: 15%`, largest card) — 4.9 stars, 10k+ adjustments, Licensed & Insured
  4. **Our Services** (right, `right: 3%`, `top: 42%`) — Spinal Adjustments, Sports Rehab, Pain Management with icons
  5. **Services** (far right, `right: -3%`, `top: 22%`, partially cut off) — Accepting New Patients
- Cards are `hidden lg:block` (only show on large screens)
- **Tagline** at bottom: "Expert chiropractic care in Westbury, NY..."

### Navbar (`components/Navbar.tsx`)
- **Fully transparent** (`bg-transparent`) — no bar, no border, no blur, no backdrop
- Nav links floats over the sky background
- Logo: Green emerald square with `Grid3X3` icon + "Action Chiro" text in white
- Links: Home, About, Services, Testimonials, Contact
- Right side: Search icon, X icon, green "Book Appointment" button
- Mobile menu uses `bg-black/20 backdrop-blur-md`

### Specialties Section (`sections/Specialties.tsx`)
- Title: "Our Chiropractic Services"
- 8 service cards: Spinal Adjustments, Sports Rehabilitation, Posture Correction, Massage Therapy, Pain Management, X-Ray & Diagnostics, Flexibility & Mobility, Pediatric & Family Care
- Each has emoji icon, title, description

### Journey Section (`sections/Journey.tsx`)
- **MissionSection:** "At Action Chiropractic P.C., we believe your body has an incredible ability to heal itself..." Mentions digital X-rays, Se habla Español
- **JourneySection:** "Your Path to Pain-Free Living"
  - Left card: Dr. Bruce C. Bromberg profile with photo + Book Appointment button
  - Center card: "Why Patients Choose Us" — 4.9 stars, Board Certified, 10k+ Adjustments
  - Right column: "Our Services" card (accepting new patients) + "Real Results" card (95% pain reduction in 3 visits)
  - Bottom row: Spinal Health, Pain Relief, Wellness, Recovery stat badges
  - Floating chiropractic emojis in background

### Top Doctors Section (`sections/TopDoctors.tsx`)
- Title: "Meet the Team Behind Your Recovery"
- Badge: "Our Care Team"
- **Award card** for Dr. Bruce C. Bromberg — "Award-Winning Chiropractor", 10k+ Adjustments, 30+ Years, mentions Westbury NY, digital X-rays, Se habla Español
- 3 team member cards: Dr. Bruce C. Bromberg (Lead), Sarah Mitchell LMT, Dr. James Chen D.C.
- Trust badge: "5k+ Happy Patients & Counting"
- Feature cards: Insurance & Billing Made Easy, Comprehensive Care Plans

### Features Section (`sections/Features.tsx`)
- Title: "What Sets Our Practice Apart"
- Left column: "Wellness Starts With Your Spine" — mentions Action Chiropractic P.C., digital X-rays
- Center: Phone mockup showing "Action Chiro" app (Next Adjustment, Progress Score, Home Exercises)
- Right: "Book Your First Visit" button + "Call 516-280-7470" + Westbury address + Se habla Español
- 4 feature cards: Personalized Treatment, Easy Scheduling, Flexible Hours, Insurance Accepted

### Contact Section (`sections/Contact.tsx`)
- **TestimonialsSection:** "What Our Patients Say" — 6 chiropractic-specific testimonials (neck injury, marathon runner, sciatica, family care, auto accident, desk worker). Paginated 3 at a time.
- Banner: "Join thousands of patients living pain-free with Action Chiropractic P.C."
- **ContactSection:** "Get In Touch" — mentions phone 516-280-7470, Westbury NY, Se habla Español
  - Left column: Office card (Action Chiropractic P.C., 179 School Street – Unit A, Westbury, NY 11590, phone/fax/email with clickable links, "Digital X-Ray On Site" + "Se habla Español" badges), Office Hours (Mon-Fri 9-6, Sat 10-2, Sun Closed), Map placeholder
  - Right column: "Request an Appointment" form with service dropdown (Initial Consultation, Spinal Adjustment, Sports Rehabilitation, etc.)

### Footer (`components/Footer.tsx`)
- Brand: "Action Chiropractic P.C." with green Grid3X3 icon
- 4 columns: Services, About, For Patients, Legal
- Social icons: Facebook, Twitter, Instagram, LinkedIn

### CSS (`index.css`)
- `animate-float` — 3s bounce (15px)
- `animate-float-gentle` — 4s bounce (10px) for larger cards
- `animate-cloud-drift` — 18s horizontal drift for cloud shapes
- Standard Tailwind base/components/utilities

### HTML (`index.html`)
- Title: "Action Chiropractic P.C. — Dr. Bruce C. Bromberg | Westbury, NY"
- Inter font weights: 400, 500, 600, 700, 800, 900

## Key Technical Details
- **Framework:** React + TypeScript + Vite
- **Styling:** Tailwind CSS
- **Animations:** Framer Motion + custom CSS keyframes
- **Doctor image:** Background removed with `rembg`, saved as RGBA PNG at `/public/dr-bromberg-hero.png` (848x1257)
- **Screenshot tool:** `python3 execution/screenshot_website.py --url "http://localhost:5173" --output ".tmp/filename.png" --viewport_width 1440 --viewport_height 900 --no_full_page`

## Design Reference
The hero section was designed to match a **Dribbble "Modern AI Healthcare" UI** reference:
- Immersive sky gradient background
- Massive outlined brand text behind a centered doctor cutout
- Floating detailed UI cards around the doctor
- Transparent navbar floating over the sky
- Clean, modern healthcare aesthetic

## What Was NOT Done / Potential Next Steps
- No real appointment booking backend
- No Google Maps embed (placeholder only)
- Team member photos are Unsplash stock (only Dr. Bromberg is real)
- No dark mode
- No mobile-specific card layouts for hero (cards are `hidden lg:block`)
- The user may want further design refinements or additional pages
