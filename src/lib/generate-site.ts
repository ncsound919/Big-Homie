/**
 * Site Generator — produces real, unique HTML sites from project descriptions.
 *
 * This is a deterministic template engine that analyzes the project description,
 * audience, and type to generate a complete, styled, standalone HTML page.
 * Every generated site is different based on the input.
 */

/* ─── Types ─── */
export interface GeneratorInput {
  name: string;
  description: string;
  type?: string;
  audience?: string;
}

export interface GeneratedSite {
  html: string;
  title: string;
  sections: string[];
  palette: string;
  businessType: string;
}

interface Palette {
  bg: string;
  surface: string;
  text: string;
  muted: string;
  accent: string;
  accentHover: string;
  hero: string;
  border: string;
}

interface BusinessProfile {
  type: string;
  heroTitle: string;
  heroSubtitle: string;
  cta: string;
  ctaSecondary: string;
  services: { title: string; desc: string; icon: string }[];
  testimonials: { text: string; name: string; role: string }[];
  stats: { value: string; label: string }[];
  aboutTitle: string;
  aboutText: string;
  contactFields: string[];
  footerTagline: string;
}

/* ─── Business Profiles ─── */
const PROFILES: Record<string, (name: string, desc: string, audience: string) => BusinessProfile> = {
  grooming: (name, _d, _a) => ({
    type: 'Pet Services',
    heroTitle: `Your Pet Deserves the Best Care`,
    heroSubtitle: `${name} provides expert grooming services that keep your furry friends looking great and feeling their best. Trusted by pet owners across the community.`,
    cta: 'Book an Appointment',
    ctaSecondary: 'View Services',
    services: [
      { title: 'Full Grooming', desc: 'Bath, haircut, nail trim, ear cleaning, and blow-dry for a complete makeover.', icon: '✂️' },
      { title: 'Bath & Brush', desc: 'Deep cleansing bath with premium shampoo, conditioning, and thorough brushing.', icon: '🛁' },
      { title: 'Nail & Paw Care', desc: 'Gentle nail trimming, filing, and paw pad moisturizing treatment.', icon: '🐾' },
      { title: 'De-shedding Treatment', desc: 'Specialized treatment to reduce shedding and keep coats healthy and smooth.', icon: '🧴' },
    ],
    testimonials: [
      { text: 'My golden retriever has never looked so good! The team is gentle, patient, and clearly loves animals.', name: 'Sarah M.', role: 'Golden Retriever Owner' },
      { text: 'Finally found a groomer my anxious poodle actually enjoys visiting. They took extra time with him and he came out looking amazing.', name: 'James K.', role: 'Poodle Owner' },
      { text: 'Professional, affordable, and my dog smells incredible for weeks. We drive 30 minutes just to come here!', name: 'Maria L.', role: 'Husky Owner' },
    ],
    stats: [
      { value: '2,500+', label: 'Happy Pets Groomed' },
      { value: '4.9★', label: 'Average Rating' },
      { value: '8+', label: 'Years Experience' },
      { value: '100%', label: 'Satisfaction Rate' },
    ],
    aboutTitle: `Why Pet Owners Choose ${name}`,
    aboutText: `We treat every pet like our own. Our certified groomers use premium, pet-safe products and take the time to understand each animal's needs. Whether your dog needs a simple bath or a full breed-specific cut, we deliver results that make tails wag.`,
    contactFields: ['Your Name', 'Pet\'s Name', 'Phone Number', 'Service Needed'],
    footerTagline: 'Where every pet gets the royal treatment',
  }),
  restaurant: (name, _d, _a) => ({
    type: 'Restaurant',
    heroTitle: `Welcome to ${name}`,
    heroSubtitle: `Crafted dishes made with locally sourced ingredients. Experience flavors that tell a story, in an atmosphere that feels like home.`,
    cta: 'Reserve a Table',
    ctaSecondary: 'See the Menu',
    services: [
      { title: 'Dine In', desc: 'Enjoy our full menu in a warm, thoughtfully designed dining space.', icon: '🍽️' },
      { title: 'Catering', desc: 'Let us bring our flavors to your events, from intimate gatherings to large celebrations.', icon: '🎉' },
      { title: 'Takeout', desc: 'Order online or by phone and pick up fresh, hot meals ready to go.', icon: '📦' },
      { title: 'Private Events', desc: 'Book our private dining room for birthdays, anniversaries, or business dinners.', icon: '🥂' },
    ],
    testimonials: [
      { text: 'The best meal I\'ve had in years. Every dish felt personal and the service was impeccable.', name: 'Michael R.', role: 'Food Critic' },
      { text: 'We come here for every special occasion. The attention to detail in both food and atmosphere is unmatched.', name: 'Diana W.', role: 'Regular Customer' },
      { text: 'Catered our wedding and guests are still talking about the food months later.', name: 'Tom & Lisa', role: 'Event Clients' },
    ],
    stats: [
      { value: '15K+', label: 'Meals Served Monthly' },
      { value: '4.8★', label: 'Google Rating' },
      { value: '12', label: 'Years Open' },
      { value: '50+', label: 'Menu Items' },
    ],
    aboutTitle: 'Our Story',
    aboutText: `${name} started with a simple belief: food tastes better when it's made with care. Our chefs source the freshest local ingredients daily, creating dishes that honor tradition while embracing creativity. Every plate is prepared with passion, and every guest is welcomed like family.`,
    contactFields: ['Your Name', 'Email', 'Date', 'Party Size'],
    footerTagline: 'Good food, great company',
  }),
  fitness: (name, _d, _a) => ({
    type: 'Fitness & Health',
    heroTitle: `Transform Your Body at ${name}`,
    heroSubtitle: `Expert personal training, group classes, and state-of-the-art equipment to help you reach your fitness goals. Start your journey today.`,
    cta: 'Start Free Trial',
    ctaSecondary: 'View Classes',
    services: [
      { title: 'Personal Training', desc: 'One-on-one sessions with certified trainers customized to your goals and fitness level.', icon: '💪' },
      { title: 'Group Classes', desc: 'High-energy classes including HIIT, yoga, spin, and strength training.', icon: '🏋️' },
      { title: 'Nutrition Coaching', desc: 'Personalized meal plans and nutrition guidance to complement your training.', icon: '🥗' },
      { title: 'Recovery Zone', desc: 'Sauna, stretching area, and recovery tools to help you bounce back faster.', icon: '🧘' },
    ],
    testimonials: [
      { text: 'Lost 40 pounds in 6 months. The trainers actually care and hold you accountable.', name: 'Chris P.', role: 'Member since 2023' },
      { text: 'Best gym I\'ve ever been to. Clean, well-equipped, and the community is incredibly supportive.', name: 'Aisha N.', role: 'Member since 2022' },
      { text: 'The group classes changed my life. I went from couch potato to running my first marathon.', name: 'Derek M.', role: 'Class Regular' },
    ],
    stats: [
      { value: '3,000+', label: 'Active Members' },
      { value: '50+', label: 'Weekly Classes' },
      { value: '98%', label: 'Retention Rate' },
      { value: '24/7', label: 'Access' },
    ],
    aboutTitle: `Why ${name}?`,
    aboutText: `We're not just a gym — we're a community committed to helping you become the best version of yourself. Every program is designed by certified professionals, every piece of equipment is meticulously maintained, and every member gets the support they need to succeed.`,
    contactFields: ['Your Name', 'Email', 'Phone', 'Fitness Goal'],
    footerTagline: 'Your goals. Our mission.',
  }),
  generic: (name, desc, audience) => ({
    type: 'Business',
    heroTitle: name,
    heroSubtitle: desc.split('Additional details:')[0].trim() || `Professional services for ${audience}. Quality you can count on, results you can see.`,
    cta: 'Get Started',
    ctaSecondary: 'Learn More',
    services: [
      { title: 'Core Service', desc: 'Our flagship offering, refined through years of experience and client feedback.', icon: '⭐' },
      { title: 'Consulting', desc: 'Expert guidance to help you make the right decisions for your needs.', icon: '💡' },
      { title: 'Support', desc: 'Responsive, dedicated support that\'s there when you need it.', icon: '🤝' },
      { title: 'Custom Solutions', desc: 'Tailored approaches built specifically for your unique situation.', icon: '🔧' },
    ],
    testimonials: [
      { text: 'Exceeded every expectation. Professional, responsive, and the results speak for themselves.', name: 'Alex T.', role: 'Client' },
      { text: 'Working with this team transformed our operations. Highly recommend to anyone serious about quality.', name: 'Jordan S.', role: 'Business Owner' },
      { text: 'Reliable, transparent, and genuinely cares about delivering great work. A rare find.', name: 'Pat M.', role: 'Long-term Client' },
    ],
    stats: [
      { value: '500+', label: 'Projects Completed' },
      { value: '4.9★', label: 'Client Rating' },
      { value: '10+', label: 'Years Experience' },
      { value: '99%', label: 'On-time Delivery' },
    ],
    aboutTitle: `About ${name}`,
    aboutText: `${name} was founded on a simple principle: deliver exceptional value without the complexity. We combine deep expertise with a client-first approach, ensuring every project is completed to the highest standard. From first contact to final delivery, we're committed to your success.`,
    contactFields: ['Your Name', 'Email', 'Phone', 'How can we help?'],
    footerTagline: 'Excellence, delivered',
  }),
};

// Extended profiles
const MORE_PROFILES: Record<string, (name: string, desc: string, audience: string) => BusinessProfile> = {
  ecommerce: (name, _d, _a) => ({
    type: 'Online Store',
    heroTitle: `Shop ${name}`,
    heroSubtitle: `Curated products, fast shipping, and hassle-free returns. Discover what everyone's talking about.`,
    cta: 'Shop Now',
    ctaSecondary: 'Browse Collections',
    services: [
      { title: 'Free Shipping', desc: 'Fast, free delivery on all orders over $50. No hidden fees, no surprises.', icon: '🚚' },
      { title: 'Easy Returns', desc: '30-day hassle-free returns on all products. Shop with confidence.', icon: '↩️' },
      { title: 'Secure Checkout', desc: 'SSL-encrypted payments with all major cards, Apple Pay, and Google Pay.', icon: '🔒' },
      { title: 'Loyalty Rewards', desc: 'Earn points on every purchase and unlock exclusive discounts and early access.', icon: '🎁' },
    ],
    testimonials: [
      { text: 'Amazing quality and the fastest shipping I\'ve experienced from any online store.', name: 'Rachel K.', role: 'Verified Buyer' },
      { text: 'Love the product selection. Everything arrives exactly as described. My go-to shop.', name: 'Marcus L.', role: 'Repeat Customer' },
      { text: 'The return process was so easy. No questions asked, full refund within days.', name: 'Linda W.', role: 'Customer' },
    ],
    stats: [
      { value: '50K+', label: 'Happy Customers' },
      { value: '4.8★', label: 'Average Review' },
      { value: '24hr', label: 'Avg Ship Time' },
      { value: '10K+', label: 'Products' },
    ],
    aboutTitle: `The ${name} Difference`,
    aboutText: `We obsess over quality so you don't have to. Every product in our catalog is hand-picked, tested, and backed by our satisfaction guarantee. We believe shopping should be simple, joyful, and risk-free.`,
    contactFields: ['Your Name', 'Email', 'Order Number', 'Message'],
    footerTagline: 'Shop smarter, live better',
  }),
  portfolio: (name, desc, _a) => ({
    type: 'Portfolio',
    heroTitle: name,
    heroSubtitle: desc.split('Additional details:')[0].trim() || `Creative professional delivering exceptional work. Let's build something incredible together.`,
    cta: 'View My Work',
    ctaSecondary: 'Contact Me',
    services: [
      { title: 'Design', desc: 'Visual design that communicates your brand story with clarity and impact.', icon: '🎨' },
      { title: 'Development', desc: 'Clean, performant code that brings designs to life on every device.', icon: '💻' },
      { title: 'Strategy', desc: 'Data-driven creative strategy that turns visitors into customers.', icon: '📊' },
      { title: 'Branding', desc: 'Complete brand identity systems from logo to guidelines.', icon: '✏️' },
    ],
    testimonials: [
      { text: 'Absolutely nailed the vision. The attention to detail and creative direction was outstanding.', name: 'Studio M.', role: 'Agency Client' },
      { text: 'Delivered ahead of schedule and above expectations. A rare combination of talent and professionalism.', name: 'TechStart', role: 'Startup Client' },
      { text: 'The rebrand transformed our entire business. Customers constantly compliment our new look.', name: 'Nora F.', role: 'Small Business Owner' },
    ],
    stats: [
      { value: '120+', label: 'Projects Shipped' },
      { value: '8', label: 'Years of Experience' },
      { value: '40+', label: 'Happy Clients' },
      { value: '15', label: 'Awards Won' },
    ],
    aboutTitle: 'About Me',
    aboutText: `I'm a creative professional who believes great work sits at the intersection of strategy and craft. Every project starts with understanding the problem, and ends with a solution that exceeds expectations. I work with brands of all sizes who are serious about standing out.`,
    contactFields: ['Your Name', 'Email', 'Project Type', 'Tell me about your project'],
    footerTagline: 'Let\'s create something remarkable',
  }),
  realestate: (name, _d, _a) => ({
    type: 'Real Estate',
    heroTitle: `Find Your Dream Home with ${name}`,
    heroSubtitle: `Expert real estate services backed by deep local knowledge. Whether buying, selling, or investing — we make it simple.`,
    cta: 'Search Properties',
    ctaSecondary: 'Free Consultation',
    services: [
      { title: 'Home Buying', desc: 'Full-service buyer representation from search to closing day celebration.', icon: '🏠' },
      { title: 'Home Selling', desc: 'Strategic pricing, professional staging, and aggressive marketing to sell fast.', icon: '🏷️' },
      { title: 'Investment', desc: 'Property investment analysis and portfolio building for long-term wealth.', icon: '📈' },
      { title: 'Relocation', desc: 'Comprehensive relocation services to make your move seamless.', icon: '🚛' },
    ],
    testimonials: [
      { text: 'Found our perfect home in just 3 weeks. The market knowledge and negotiation skills were incredible.', name: 'The Johnsons', role: 'First-time Buyers' },
      { text: 'Sold 15% above asking price in under a week. The marketing strategy was brilliant.', name: 'Robert C.', role: 'Home Seller' },
      { text: 'Managed our entire relocation from out of state. Couldn\'t have done it without this team.', name: 'Angela M.', role: 'Relocation Client' },
    ],
    stats: [
      { value: '$85M+', label: 'In Sales Volume' },
      { value: '350+', label: 'Homes Sold' },
      { value: '12', label: 'Days Avg on Market' },
      { value: '98%', label: 'List-to-Sale Ratio' },
    ],
    aboutTitle: `Why ${name}`,
    aboutText: `Real estate is more than transactions — it's about finding where life happens. With deep community roots and a track record of results, we guide you through every step of the process with transparency, expertise, and genuine care.`,
    contactFields: ['Your Name', 'Email', 'Phone', 'What are you looking for?'],
    footerTagline: 'Your home journey starts here',
  }),
  gaming: (name, _d, _a) => ({
    type: 'Gaming',
    heroTitle: `Welcome to ${name}`,
    heroSubtitle: `Next-level gaming experiences, epic communities, and the latest in interactive entertainment. Your adventure starts here.`,
    cta: 'Play Now',
    ctaSecondary: 'Explore Games',
    services: [
      { title: 'Multiplayer', desc: 'Squad up with friends or match with players worldwide in real-time competitive and cooperative modes.', icon: '🎮' },
      { title: 'Tournaments', desc: 'Compete in ranked tournaments with prize pools, leaderboards, and live broadcasts.', icon: '🏆' },
      { title: 'Game Library', desc: 'Hundreds of titles across genres — from fast-paced shooters to immersive RPGs and casual puzzlers.', icon: '📚' },
      { title: 'Community', desc: 'Join guilds, create clans, share content, and connect with gamers who share your passion.', icon: '👥' },
    ],
    testimonials: [
      { text: 'The matchmaking is insanely fast and the community is actually chill. Best gaming platform I\'ve used.', name: 'Tyler R.', role: 'Competitive Player' },
      { text: 'I\'ve been gaming for 15 years and this is the smoothest experience I\'ve had. Zero lag, great UI.', name: 'Mika S.', role: 'Streamer' },
      { text: 'My kids and I play together every weekend. The family-friendly options are a huge plus.', name: 'Dave H.', role: 'Casual Gamer' },
    ],
    stats: [
      { value: '2M+', label: 'Active Players' },
      { value: '500+', label: 'Games Available' },
      { value: '99.9%', label: 'Uptime' },
      { value: '24/7', label: 'Live Support' },
    ],
    aboutTitle: `About ${name}`,
    aboutText: `${name} was built by gamers, for gamers. We believe gaming should be accessible, exciting, and community-driven. Whether you're a casual player unwinding after work or a competitive esports athlete pushing for the top — this is your home.`,
    contactFields: ['Gamertag', 'Email', 'Platform', 'How can we help?'],
    footerTagline: 'Game on.',
  }),
  education: (name, _d, _a) => ({
    type: 'Education',
    heroTitle: `Learn Without Limits at ${name}`,
    heroSubtitle: `Expert-led courses, hands-on projects, and a supportive community to help you master new skills and advance your career.`,
    cta: 'Start Learning',
    ctaSecondary: 'Browse Courses',
    services: [
      { title: 'Online Courses', desc: 'Self-paced video courses with quizzes, projects, and certificates of completion.', icon: '🎓' },
      { title: 'Live Workshops', desc: 'Interactive live sessions with instructors for real-time Q&A and hands-on practice.', icon: '📡' },
      { title: 'Mentorship', desc: 'One-on-one guidance from industry professionals who help you stay on track.', icon: '🧑‍🏫' },
      { title: 'Career Services', desc: 'Resume reviews, interview prep, and job placement support to launch your career.', icon: '💼' },
    ],
    testimonials: [
      { text: 'Went from zero coding knowledge to a full-time developer role in 8 months. The curriculum is that good.', name: 'Priya K.', role: 'Career Changer' },
      { text: 'The mentorship made all the difference. Having someone to guide me through the tough parts kept me going.', name: 'Marcus J.', role: 'Student' },
      { text: 'I\'ve taken courses on every major platform. This one actually delivers on its promises.', name: 'Elena T.', role: 'Lifelong Learner' },
    ],
    stats: [
      { value: '50K+', label: 'Students Enrolled' },
      { value: '200+', label: 'Courses Available' },
      { value: '4.8★', label: 'Avg Course Rating' },
      { value: '92%', label: 'Completion Rate' },
    ],
    aboutTitle: `Why ${name}?`,
    aboutText: `Education should be accessible, practical, and actually enjoyable. ${name} combines world-class instructors with project-based learning so you don't just memorize — you build. Every course is designed to give you skills employers actually want.`,
    contactFields: ['Your Name', 'Email', 'Interest Area', 'What are your learning goals?'],
    footerTagline: 'Your future starts with the next lesson',
  }),
  salon: (name, _d, _a) => ({
    type: 'Beauty & Salon',
    heroTitle: `Look Your Best at ${name}`,
    heroSubtitle: `Premium beauty services in a relaxing atmosphere. From cuts and color to spa treatments, we help you look and feel amazing.`,
    cta: 'Book Now',
    ctaSecondary: 'View Services',
    services: [
      { title: 'Hair Styling', desc: 'Cuts, color, highlights, balayage, and blowouts from experienced stylists.', icon: '💇' },
      { title: 'Nail Services', desc: 'Manicures, pedicures, gel, acrylics, and nail art in a clean, relaxing setting.', icon: '💅' },
      { title: 'Spa Treatments', desc: 'Facials, massages, body wraps, and skincare consultations for total relaxation.', icon: '🧖' },
      { title: 'Bridal Packages', desc: 'Complete bridal beauty packages including hair, makeup, and day-of touch-ups.', icon: '👰' },
    ],
    testimonials: [
      { text: 'Best haircut I\'ve ever gotten. The stylist actually listened and nailed exactly what I wanted.', name: 'Jasmine R.', role: 'Regular Client' },
      { text: 'Did my bridal party\'s hair and makeup. Everyone looked stunning and the team was so professional.', name: 'Nicole P.', role: 'Bride' },
      { text: 'The spa facial changed my skin. I\'ve been coming back monthly and the results are incredible.', name: 'Laura K.', role: 'Spa Client' },
    ],
    stats: [
      { value: '8K+', label: 'Happy Clients' },
      { value: '4.9★', label: 'Rating' },
      { value: '15+', label: 'Stylists' },
      { value: '10', label: 'Years Open' },
    ],
    aboutTitle: `The ${name} Experience`,
    aboutText: `${name} is more than a salon — it's a sanctuary. Our team of licensed professionals stays on top of the latest trends and techniques to deliver results that make you feel confident. Every visit is personalized to your style, your needs, and your schedule.`,
    contactFields: ['Your Name', 'Phone', 'Service', 'Preferred Date/Time'],
    footerTagline: 'Where beauty meets confidence',
  }),
  tech: (name, desc, _a) => ({
    type: 'Technology',
    heroTitle: `Build Faster with ${name}`,
    heroSubtitle: desc.split('Additional details:')[0].trim() || `Modern software tools and infrastructure that help teams ship better products, faster. Developer-first, enterprise-ready.`,
    cta: 'Get Started Free',
    ctaSecondary: 'See Docs',
    services: [
      { title: 'API Platform', desc: 'RESTful and GraphQL APIs with automatic documentation, rate limiting, and versioning.', icon: '⚡' },
      { title: 'Cloud Infrastructure', desc: 'Scalable hosting with auto-scaling, CDN, and 99.99% uptime SLA.', icon: '☁️' },
      { title: 'Developer Tools', desc: 'CLI, SDKs, and integrations with your favorite tools — from VS Code to GitHub.', icon: '🛠️' },
      { title: 'Analytics', desc: 'Real-time dashboards, custom metrics, and alerts to monitor what matters.', icon: '📊' },
    ],
    testimonials: [
      { text: 'Cut our deployment time from hours to minutes. The DX is phenomenal.', name: 'Engineering Team', role: 'Series B Startup' },
      { text: 'Finally a platform that doesn\'t require a DevOps team to manage. It just works.', name: 'Sarah L.', role: 'Solo Founder' },
      { text: 'We migrated our entire stack in a weekend. The docs are that good.', name: 'Kevin M.', role: 'CTO' },
    ],
    stats: [
      { value: '10K+', label: 'Developers' },
      { value: '99.99%', label: 'Uptime' },
      { value: '50ms', label: 'Avg Latency' },
      { value: '1B+', label: 'API Calls/mo' },
    ],
    aboutTitle: `Why ${name}?`,
    aboutText: `We're developers who got tired of duct-taping tools together. ${name} is the platform we wished existed — fast, reliable, and designed to stay out of your way so you can focus on building great products.`,
    contactFields: ['Your Name', 'Email', 'Company', 'Tell us about your project'],
    footerTagline: 'Ship it.',
  }),
  medical: (name, _d, _a) => ({
    type: 'Healthcare',
    heroTitle: `Your Health, Our Priority — ${name}`,
    heroSubtitle: `Compassionate, comprehensive healthcare for you and your family. Modern facilities, experienced providers, and a genuine commitment to your wellbeing.`,
    cta: 'Book Appointment',
    ctaSecondary: 'Our Services',
    services: [
      { title: 'Primary Care', desc: 'Routine checkups, preventive care, chronic condition management, and health screenings.', icon: '🩺' },
      { title: 'Urgent Care', desc: 'Walk-in availability for non-emergency illnesses and injuries — no appointment needed.', icon: '🏥' },
      { title: 'Telehealth', desc: 'Virtual appointments from the comfort of your home with the same quality care.', icon: '💻' },
      { title: 'Specialist Referrals', desc: 'Seamless referrals to trusted specialists with coordinated care every step of the way.', icon: '📋' },
    ],
    testimonials: [
      { text: 'The doctors here actually take time to listen. I never feel rushed during my appointments.', name: 'Rebecca S.', role: 'Patient' },
      { text: 'Telehealth saved me so much time with two young kids. The care is just as thorough as in-person.', name: 'Amanda G.', role: 'Parent' },
      { text: 'From scheduling to follow-up, the entire experience is smooth and professional.', name: 'Howard T.', role: 'Long-time Patient' },
    ],
    stats: [
      { value: '25K+', label: 'Patients Served' },
      { value: '4.9★', label: 'Patient Rating' },
      { value: '20+', label: 'Providers' },
      { value: 'Same Day', label: 'Appointments' },
    ],
    aboutTitle: `About ${name}`,
    aboutText: `${name} was founded on the belief that quality healthcare should be accessible and personal. Our team of board-certified physicians and nurse practitioners combines modern medicine with old-fashioned care — treating you as a person, not just a chart number.`,
    contactFields: ['Patient Name', 'Phone', 'Insurance Provider', 'Reason for Visit'],
    footerTagline: 'Caring for you and yours',
  }),
  legal: (name, _d, _a) => ({
    type: 'Legal Services',
    heroTitle: `${name} — Trusted Legal Counsel`,
    heroSubtitle: `Experienced attorneys providing clear, strategic legal guidance. We fight for your rights and work tirelessly to achieve the best possible outcome.`,
    cta: 'Free Consultation',
    ctaSecondary: 'Practice Areas',
    services: [
      { title: 'Business Law', desc: 'Entity formation, contracts, compliance, and litigation for businesses of all sizes.', icon: '⚖️' },
      { title: 'Personal Injury', desc: 'Aggressive representation to get you the compensation you deserve after an accident.', icon: '🛡️' },
      { title: 'Family Law', desc: 'Divorce, custody, adoption, and family mediation handled with sensitivity and care.', icon: '👨‍👩‍👧' },
      { title: 'Estate Planning', desc: 'Wills, trusts, powers of attorney, and probate to protect your family\'s future.', icon: '📜' },
    ],
    testimonials: [
      { text: 'Won my case and got me a settlement I never thought possible. Professional and aggressive when it counted.', name: 'Marcus D.', role: 'Personal Injury Client' },
      { text: 'Guided us through a complex business acquisition seamlessly. Worth every penny.', name: 'Greenfield Corp.', role: 'Corporate Client' },
      { text: 'Handled my divorce with compassion and got a fair outcome for my kids. Forever grateful.', name: 'Jennifer S.', role: 'Family Law Client' },
    ],
    stats: [
      { value: '2,000+', label: 'Cases Won' },
      { value: '$150M+', label: 'Recovered for Clients' },
      { value: '30+', label: 'Years Combined Exp' },
      { value: '5★', label: 'Avvo Rating' },
    ],
    aboutTitle: `Why Choose ${name}?`,
    aboutText: `The law can be intimidating. We make it approachable. ${name} combines deep legal expertise with straightforward communication — you'll always know where your case stands and what comes next. Your first consultation is always free.`,
    contactFields: ['Your Name', 'Phone', 'Case Type', 'Brief Description'],
    footerTagline: 'Justice, one case at a time',
  }),
};

/* ─── Detection ─── */
function detectBusinessType(desc: string, type: string, name: string): string {
  const text = `${name} ${desc} ${type}`.toLowerCase();
  if (/game|gaming|gamer|esport|video\s*game|arcade|xbox|playstation|steam|twitch|rpg|mmorpg/i.test(text)) return 'gaming';
  if (/groom|pet|dog|cat|animal|vet|kennel/i.test(text)) return 'grooming';
  if (/restaurant|food|cafe|coffee|bakery|pizza|sushi|dine|catering|bistro|bar\b|grill/i.test(text)) return 'restaurant';
  if (/gym|fitness|workout|training|yoga|crossfit/i.test(text)) return 'fitness';
  if (/shop|store|ecommerce|e-commerce|product|retail|buy|sell|merch/i.test(text)) return 'ecommerce';
  if (/portfolio|freelance|artist|designer|photographer|creative|my work|showcase/i.test(text)) return 'portfolio';
  if (/real\s*estate|property|homes|realt|housing|apartment|condo/i.test(text)) return 'realestate';
  if (/school|course|learn|education|tutor|academ|university|class|lesson|training\s*program/i.test(text)) return 'education';
  if (/salon|beauty|hair|nail|spa|skin|facial|stylist|barber|makeup/i.test(text)) return 'salon';
  if (/saas|software|api|platform|dev|startup|tech|cloud|app\b|infra/i.test(text)) return 'tech';
  if (/doctor|medical|clinic|health|hospital|patient|dental|dentist|therap|chiro|optom/i.test(text)) return 'medical';
  if (/law|legal|attorney|lawyer|firm|litigation|counsel/i.test(text)) return 'legal';
  return 'generic';
}

function detectPalette(desc: string): Palette {
  const text = desc.toLowerCase();
  if (/bold|colorful|vibrant|neon|bright|vivid|fun|playful/i.test(text)) {
    return { bg: '#0a0a12', surface: '#15152a', text: '#f0f0ff', muted: '#9090b0', accent: '#e040a0', accentHover: '#f050b0', hero: 'linear-gradient(135deg, #7c3aed 0%, #e040a0 50%, #f59e0b 100%)', border: '#2a2a45' };
  }
  if (/clean|minimal|simple|white|light|modern|professional/i.test(text)) {
    return { bg: '#ffffff', surface: '#f8f9fa', text: '#1a1a2e', muted: '#6b7280', accent: '#4f46e5', accentHover: '#4338ca', hero: 'linear-gradient(135deg, #4f46e5, #7c3aed)', border: '#e5e7eb' };
  }
  if (/warm|earth|natural|organic|cozy|rustic/i.test(text)) {
    return { bg: '#1a1410', surface: '#231e18', text: '#f5efe6', muted: '#a89a8a', accent: '#d97706', accentHover: '#f59e0b', hero: 'linear-gradient(135deg, #92400e, #d97706)', border: '#3d3428' };
  }
  if (/luxury|elegant|premium|gold|upscale|exclusive/i.test(text)) {
    return { bg: '#0c0c0c', surface: '#1a1a1a', text: '#f5f0e8', muted: '#9a9080', accent: '#c8a960', accentHover: '#dabb70', hero: 'linear-gradient(135deg, #1a1a2e, #c8a960)', border: '#2a2a28' };
  }
  // Default dark
  return { bg: '#0f1117', surface: '#181a24', text: '#eef0f6', muted: '#8890a4', accent: '#3b82f6', accentHover: '#60a5fa', hero: 'linear-gradient(135deg, #1e3a8a, #3b82f6)', border: '#252830' };
}

/* ─── HTML Generator ─── */
export function generateSite(input: GeneratorInput): GeneratedSite {
  const { name, description, type = 'Website', audience = 'everyone' } = input;
  const bizType = detectBusinessType(description, type, name);
  const allProfiles = { ...PROFILES, ...MORE_PROFILES };
  const profile = (allProfiles[bizType] || allProfiles.generic)(name, description, audience);
  const p = detectPalette(description);

  const sections = ['hero', 'stats', 'services', 'about', 'testimonials', 'cta', 'contact', 'footer'];

  const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>${esc(name)} — ${esc(profile.type)}</title>
<meta name="description" content="${esc(profile.heroSubtitle.slice(0, 160))}">
<meta property="og:title" content="${esc(name)}">
<meta property="og:description" content="${esc(profile.heroSubtitle.slice(0, 200))}">
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:${p.bg};--surface:${p.surface};--text:${p.text};--muted:${p.muted};
  --accent:${p.accent};--accent-hover:${p.accentHover};--hero:${p.hero};--border:${p.border};
}
html{scroll-behavior:smooth}
body{font-family:ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--bg);color:var(--text);line-height:1.6;-webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration:none}
img{max-width:100%;display:block}
.container{max-width:1120px;margin:0 auto;padding:0 24px}

/* Nav */
.nav{position:fixed;top:0;left:0;right:0;z-index:50;padding:0 24px;height:64px;display:flex;align-items:center;justify-content:space-between;background:${p.bg}e6;backdrop-filter:blur(16px);border-bottom:1px solid var(--border)}
.nav-brand{font-weight:800;font-size:20px;letter-spacing:-0.5px}
.nav-links{display:flex;gap:28px;font-size:14px;color:var(--muted)}
.nav-links a:hover{color:var(--text)}
.nav-cta{padding:8px 20px;border-radius:8px;background:var(--accent);color:#fff;font-weight:600;font-size:13px;border:none;cursor:pointer;transition:background 0.2s}
.nav-cta:hover{background:var(--accent-hover)}

/* Hero */
.hero{padding:160px 24px 100px;text-align:center;position:relative;overflow:hidden}
.hero::before{content:'';position:absolute;top:5%;left:50%;transform:translateX(-50%);width:700px;height:700px;border-radius:50%;background:var(--hero);opacity:0.1;filter:blur(100px);pointer-events:none}
.hero-badge{display:inline-block;padding:6px 16px;border-radius:999px;background:${p.accent}18;color:var(--accent);font-size:12px;font-weight:600;letter-spacing:0.05em;text-transform:uppercase;margin-bottom:24px}
.hero h1{font-size:clamp(2.5rem,6vw,4.5rem);font-weight:900;line-height:1.08;letter-spacing:-2px;margin-bottom:20px;background:var(--hero);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.hero p{font-size:clamp(1rem,2vw,1.15rem);color:var(--muted);max-width:580px;margin:0 auto 36px;line-height:1.7}
.hero-btns{display:flex;gap:12px;justify-content:center;flex-wrap:wrap}
.btn-primary{padding:14px 32px;border-radius:10px;background:var(--hero);color:#fff;font-weight:700;font-size:15px;border:none;cursor:pointer;transition:transform 0.2s,opacity 0.2s}
.btn-primary:hover{transform:translateY(-2px);opacity:0.9}
.btn-secondary{padding:14px 32px;border-radius:10px;background:transparent;color:var(--text);font-weight:600;font-size:15px;border:1px solid var(--border);cursor:pointer;transition:border-color 0.2s}
.btn-secondary:hover{border-color:var(--accent)}

/* Stats */
.stats{padding:60px 24px;border-bottom:1px solid var(--border)}
.stats-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:24px;max-width:900px;margin:0 auto;text-align:center}
.stat-val{font-size:2rem;font-weight:900;letter-spacing:-1px;background:var(--hero);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.stat-label{font-size:13px;color:var(--muted);margin-top:4px}

/* Services */
.services{padding:100px 24px}
.section-title{text-align:center;font-size:clamp(1.5rem,3vw,2.4rem);font-weight:800;letter-spacing:-1px;margin-bottom:12px}
.section-sub{text-align:center;color:var(--muted);margin-bottom:56px;font-size:16px}
.services-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:20px}
.service-card{padding:32px;border-radius:16px;background:var(--surface);border:1px solid var(--border);transition:transform 0.25s,border-color 0.25s}
.service-card:hover{transform:translateY(-4px);border-color:var(--accent)}
.service-icon{width:48px;height:48px;border-radius:12px;background:${p.accent}14;display:flex;align-items:center;justify-content:center;font-size:22px;margin-bottom:16px}
.service-card h3{font-weight:700;font-size:16px;margin-bottom:8px}
.service-card p{color:var(--muted);font-size:14px;line-height:1.6}

/* About */
.about{padding:100px 24px}
.about-inner{display:grid;grid-template-columns:1fr 1fr;gap:60px;align-items:center;max-width:1000px;margin:0 auto}
.about-img{aspect-ratio:4/3;border-radius:20px;background:var(--hero);opacity:0.8}
.about h2{font-size:clamp(1.4rem,3vw,2rem);font-weight:800;letter-spacing:-0.5px;margin-bottom:16px}
.about p{color:var(--muted);font-size:15px;line-height:1.7}

/* Testimonials */
.testimonials{padding:100px 24px}
.testimonials-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px}
.testimonial{padding:32px;border-radius:16px;background:var(--surface);border:1px solid var(--border)}
.testimonial blockquote{font-size:15px;line-height:1.7;color:var(--text);margin-bottom:20px;font-style:italic}
.testimonial-author{font-weight:700;font-size:14px}
.testimonial-role{font-size:12px;color:var(--muted)}

/* CTA Banner */
.cta-banner{padding:60px 24px}
.cta-inner{max-width:800px;margin:0 auto;padding:60px 48px;border-radius:24px;background:var(--hero);text-align:center;position:relative;overflow:hidden}
.cta-inner::before{content:'';position:absolute;inset:0;background:rgba(0,0,0,0.3)}
.cta-inner>*{position:relative;z-index:1}
.cta-inner h2{font-size:clamp(1.5rem,3vw,2.2rem);font-weight:900;color:#fff;margin-bottom:12px;letter-spacing:-0.5px}
.cta-inner p{color:rgba(255,255,255,0.75);margin-bottom:28px;font-size:16px}
.btn-white{padding:14px 36px;border-radius:10px;background:#fff;color:#1a1a2e;font-weight:700;font-size:15px;border:none;cursor:pointer;transition:transform 0.2s}
.btn-white:hover{transform:translateY(-2px)}

/* Contact */
.contact{padding:100px 24px}
.contact-form{max-width:500px;margin:0 auto;display:flex;flex-direction:column;gap:16px}
.contact-form input,.contact-form textarea{padding:14px 18px;border-radius:10px;border:1px solid var(--border);background:var(--surface);color:var(--text);font-size:14px;font-family:inherit;outline:none;transition:border-color 0.2s}
.contact-form input:focus,.contact-form textarea:focus{border-color:var(--accent)}
.contact-form textarea{min-height:120px;resize:vertical}
.contact-note{color:var(--muted);font-size:12px;text-align:center}

/* Footer */
.footer{border-top:1px solid var(--border);padding:32px 24px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px}
.footer-brand{font-weight:700;font-size:16px}
.footer-tag{color:var(--muted);font-size:12px}
.footer-built{color:var(--muted);font-size:11px;opacity:0.6}

/* Responsive */
@media(max-width:768px){
  .stats-grid{grid-template-columns:repeat(2,1fr)}
  .about-inner{grid-template-columns:1fr;gap:32px}
  .nav-links{display:none}
}
@media(max-width:480px){
  .stats-grid{grid-template-columns:1fr 1fr}
  .hero h1{font-size:2.2rem;letter-spacing:-1px}
}
</style>
</head>
<body>

<!-- Nav -->
<nav class="nav">
  <span class="nav-brand">${esc(name)}</span>
  <div class="nav-links">
    <a href="#services">Services</a>
    <a href="#about">About</a>
    <a href="#testimonials">Reviews</a>
    <a href="#contact">Contact</a>
  </div>
  <button class="nav-cta">${esc(profile.cta)}</button>
</nav>

<!-- Hero -->
<section class="hero" id="hero">
  <div class="hero-badge">${esc(profile.type)} ✦</div>
  <h1>${esc(profile.heroTitle)}</h1>
  <p>${esc(profile.heroSubtitle)}</p>
  <div class="hero-btns">
    <button class="btn-primary">${esc(profile.cta)} →</button>
    <button class="btn-secondary">${esc(profile.ctaSecondary)}</button>
  </div>
</section>

<!-- Stats -->
<section class="stats" id="stats">
  <div class="stats-grid">
    ${profile.stats.map(s => `<div><div class="stat-val">${esc(s.value)}</div><div class="stat-label">${esc(s.label)}</div></div>`).join('\n    ')}
  </div>
</section>

<!-- Services -->
<section class="services" id="services">
  <div class="container">
    <h2 class="section-title">What We Offer</h2>
    <p class="section-sub">Everything you need, nothing you don't.</p>
    <div class="services-grid">
      ${profile.services.map(s => `<div class="service-card">
        <div class="service-icon">${s.icon}</div>
        <h3>${esc(s.title)}</h3>
        <p>${esc(s.desc)}</p>
      </div>`).join('\n      ')}
    </div>
  </div>
</section>

<!-- About -->
<section class="about" id="about">
  <div class="about-inner">
    <div class="about-img"></div>
    <div>
      <h2>${esc(profile.aboutTitle)}</h2>
      <p>${esc(profile.aboutText)}</p>
    </div>
  </div>
</section>

<!-- Testimonials -->
<section class="testimonials" id="testimonials">
  <div class="container">
    <h2 class="section-title">What People Say</h2>
    <p class="section-sub">Don't take our word for it — hear from those who matter.</p>
    <div class="testimonials-grid">
      ${profile.testimonials.map(t => `<div class="testimonial">
        <blockquote>"${esc(t.text)}"</blockquote>
        <div class="testimonial-author">${esc(t.name)}</div>
        <div class="testimonial-role">${esc(t.role)}</div>
      </div>`).join('\n      ')}
    </div>
  </div>
</section>

<!-- CTA Banner -->
<section class="cta-banner">
  <div class="cta-inner">
    <h2>Ready to Get Started?</h2>
    <p>Join the people who already trust ${esc(name)}.</p>
    <button class="btn-white">${esc(profile.cta)} →</button>
  </div>
</section>

<!-- Contact -->
<section class="contact" id="contact">
  <div class="container">
    <h2 class="section-title">Get in Touch</h2>
    <p class="section-sub">We'd love to hear from you.</p>
    <form class="contact-form">
      ${profile.contactFields.slice(0, 3).map(f => `<input type="text" placeholder="${esc(f)}" required>`).join('\n      ')}
      <textarea placeholder="${esc(profile.contactFields[3] || 'Message')}"></textarea>
      <button class="btn-primary" type="button">Send Message →</button>
      <p class="contact-note">Preview only. Connect this form to your inbox or CRM when deploying.</p>
    </form>
  </div>
</section>

<!-- Footer -->
<footer class="footer">
  <span class="footer-brand">${esc(name)}</span>
  <span class="footer-tag">${esc(profile.footerTagline)}</span>
  <span class="footer-built">Built with AgentBrowser · ${new Date().getFullYear()}</span>
</footer>

</body>
</html>`;

  return { html, title: `${name} — ${profile.type}`, sections, palette: p.accent, businessType: bizType };
}

function esc(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
