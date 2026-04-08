import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';

test.describe('BullVPN Login Automation Tests', () => {
  
  /////////////////// Case 1: กรอกถูก ต้องเข้า Dashboard ได้ ///////////////////
  test('Success Login', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login('smildd', '09876512345Am@');
    await expect(page).toHaveURL(/.*account/);
  });

  /////////////////// Case 2: กรอกผิด ต้องแสดงข้อความแจ้งเตือน ///////////////////
  test('Invalid Credentials', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login('smildd', '09876512345Am');
    await expect(page.getByText('Username or password is invalid')).toBeVisible();
  });

  /////////////////// Case 3: ไม่กรอกข้อมูลอะไรเลยแล้วกด Login ///////////////////
  test('Empty Fields Validation', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.loginButton.click();
    await expect(page).toHaveURL(/.*login/); 
  });
  /////////////////// Case 4: ทดสอบปุ่มดูรหัสผ่าน ///////////////////
  test('Password Visibility Toggle', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.passwordInput.fill('secret123');
    await page.locator('.fa-eye').click(); 
    await expect(loginPage.passwordInput).toHaveAttribute('type', 'text');
  });
  /////////////////// Case 5: เช็คการโหลดหน้าเว็บ ///////////////////
  test('UI Elements are Visible', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await expect(loginPage.usernameInput).toBeVisible();
    await expect(loginPage.passwordInput).toBeVisible();
    await expect(loginPage.loginButton).toBeVisible();
  });
  /////////////////// Case 6: เช็ค Format อีเมล///////////////////
  test('Invalid Email Format Validation', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.usernameInput.fill('wrongemailformat.com');
    await loginPage.passwordInput.fill('password123');
    await page.pause(); 
    await loginPage.loginButton.click();
    await expect(page).toHaveURL(/.*login/);
    await expect(page.getByText('Username or password is invalid').first()).toBeVisible();
  });
  /////////////////// Case 7: เช็คความปลอดภัยของเว็บไซต์ ///////////////////
  test('Website Authenticity (Security Check)', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await expect(page).toHaveURL('https://www.bullvpn.com/login');
    await expect(page).toHaveTitle(/Login.*BullVPN/i);
  });
  /////////////////// Case 8: เช็คการนำทางด้วยคีย์บอร์ด  ///////////////////
  test('Keyboard Navigation (Accessibility Test)', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.usernameInput.focus();
    await page.keyboard.type('mild_tester');
    await page.keyboard.press('Tab');
    await page.keyboard.type('password123');
    await page.pause(); 
    await loginPage.loginButton.focus(); 
    await page.keyboard.press('Enter'); 
    await expect(page.getByText('Username or password is invalid').first()).toBeVisible();
  });
  /////////////////// Case 9: เช็คการป้องกันการโจมตีแบบ SQL Injection ///////////////////
  test('Security Check (SQL Injection Prevention)', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.usernameInput.fill("' OR '1'='1");
    await loginPage.passwordInput.fill("admin'--");
    await page.pause(); // แวะกด Captcha
    await loginPage.loginButton.click();
    await expect(page.getByText('Username or password is invalid').first()).toBeVisible();
  });
  /////////////////// Case 10: เช็คลิงก์นำทาง ///////////////////
  test('Navigation Links Validation (Forgot Password & Register)', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    const forgotPasswordLink = page.getByText('Forgot your password?');
    await expect(forgotPasswordLink).toHaveAttribute('href', /.*forgot/); 
    const registerLink = page.getByText('Register');
    await expect(registerLink).toBeVisible();
  });
});