import { test, expect } from '@playwright/test';

test.describe('HARV Frontend E2E Tests', () => {
  test('should load landing page', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('h1')).toContainText('HARV Demo Dashboard');
    await expect(page.locator('text=Professor Mode')).toBeVisible();
    await expect(page.locator('text=Student Mode')).toBeVisible();
  });

  test('should navigate to professor mode', async ({ page }) => {
    await page.goto('/');
    await page.click('text=Professor Mode');
    await expect(page).toHaveURL('/professor');
    await expect(page.locator('h1')).toContainText('Professor Mode');
    await expect(page.locator('text=Calibrate Classroom Location')).toBeVisible();
  });

  test('should navigate to student mode', async ({ page }) => {
    await page.goto('/');
    await page.click('text=Student Mode');
    await expect(page).toHaveURL('/student');
    await expect(page.locator('h1')).toContainText('Student Mode');
    await expect(page.locator('text=Geolocation-first Auth')).toBeVisible();
  });

  test('should navigate to status page', async ({ page }) => {
    await page.goto('/');
    await page.click('text=Status');
    await expect(page).toHaveURL('/status');
    await expect(page.locator('h1')).toContainText('System Status');
  });

  test('professor calibration form should have inputs', async ({ page }) => {
    await page.goto('/professor');
    await expect(page.locator('input[type="number"]').nth(0)).toBeVisible(); // Latitude
    await expect(page.locator('input[type="number"]').nth(1)).toBeVisible(); // Longitude
    await expect(page.locator('input[type="number"]').nth(2)).toBeVisible(); // Epsilon
    await expect(page.locator('button:has-text("Save Calibration")')).toBeVisible();
  });

  test('student mode should have verification methods', async ({ page }) => {
    await page.goto('/student');
    await expect(page.locator('input[value="gps"]')).toBeVisible();
    await expect(page.locator('input[value="ip"]')).toBeVisible();
    await expect(page.locator('text=Image Verification')).toBeVisible();
  });

  test('GPS button should request geolocation with mock', async ({ page, context }) => {
    // Grant geolocation permission and mock coordinates
    await context.grantPermissions(['geolocation']);
    await context.setGeolocation({ latitude: 42.3771, longitude: -71.1166 });

    await page.goto('/student');
    
    // Click GPS button
    const gpsButton = page.locator('button:has-text("Get My GPS Location")');
    await expect(gpsButton).toBeVisible();
    await gpsButton.click();

    // Wait for GPS to be acquired
    await page.waitForSelector('text=GPS acquired', { timeout: 5000 });
    await expect(page.locator('text=Latitude: 42.377')).toBeVisible();
  });

  test('image verification form should accept file upload', async ({ page }) => {
    await page.goto('/student');
    
    const fileInput = page.locator('input[type="file"]');
    await expect(fileInput).toBeVisible();
    
    const challengeInput = page.locator('input[value="orchid"]');
    await expect(challengeInput).toBeVisible();
  });
});
