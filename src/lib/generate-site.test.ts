import { describe, expect, it } from 'vitest';
import { generateSite } from '@/lib/generate-site';

describe('generateSite', () => {
  it('generates industry-specific content', () => {
    const grooming = generateSite({
      name: 'Happy Paws',
      description: 'Dog grooming website for busy pet owners in the city.',
      type: 'Business Website',
      audience: 'Pet owners',
    });

    const restaurant = generateSite({
      name: 'Oak Table',
      description: 'Modern restaurant with seasonal tasting menus.',
      type: 'Restaurant Website',
      audience: 'Local diners',
    });

    expect(grooming.businessType).toBe('grooming');
    expect(grooming.html).toContain('Full Grooming');
    expect(grooming.html).toContain('Pet Services');

    expect(restaurant.businessType).toBe('restaurant');
    expect(restaurant.html).toContain('Reserve a Table');
    expect(restaurant.html).not.toContain('Full Grooming');
  });

  it('detects gaming from project name even without keywords in description', () => {
    const site = generateSite({
      name: 'vid game',
      description: 'A cool new project for players who like to compete.',
      type: 'Website',
      audience: 'Gamers',
    });

    expect(site.businessType).toBe('gaming');
    expect(site.html).toContain('Play Now');
    expect(site.html).toContain('Multiplayer');
    expect(site.html).not.toContain('Full Grooming');
    expect(site.html).not.toContain('Pet Services');
  });

  it('detects all supported business types', () => {
    const cases: [string, string, string][] = [
      ['My Gym', 'Fitness center', 'fitness'],
      ['ShopNow', 'Online store for shoes', 'ecommerce'],
      ['Jane Doe', 'Freelance designer portfolio', 'portfolio'],
      ['HomeFind', 'Real estate listings', 'realestate'],
      ['EpicPlay', 'Video game community', 'gaming'],
      ['CodeAcademy', 'Online courses for learning to code', 'education'],
      ['Style Studio', 'Hair salon and spa', 'salon'],
      ['CloudAPI', 'SaaS platform for developers', 'tech'],
      ['CityClinic', 'Family medical clinic', 'medical'],
      ['Smith & Associates', 'Law firm for business litigation', 'legal'],
    ];

    for (const [name, desc, expected] of cases) {
      const site = generateSite({ name, description: desc });
      expect(site.businessType, `"${name}: ${desc}" should be ${expected}`).toBe(expected);
    }
  });

  it('escapes user input and avoids inline script dependencies', () => {
    const site = generateSite({
      name: '<script>alert(1)</script>',
      description: 'Clean portfolio for <b>unsafe</b> content.',
      type: 'Portfolio',
      audience: 'Clients',
    });

    expect(site.html).toContain('&lt;script&gt;alert(1)&lt;/script&gt;');
    expect(site.html).not.toContain('onsubmit=');
    expect(site.html).not.toContain('fonts.googleapis.com');
  });
});