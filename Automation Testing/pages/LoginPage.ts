import { Page, Locator } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  readonly usernameInput: Locator;
  readonly passwordInput: Locator;
  readonly loginButton: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.usernameInput = page.locator('#username'); 
    this.passwordInput = page.locator('#password');
    this.loginButton = page.locator('#btn-submit-login');
    this.errorMessage = page.locator('.help-block').first();
  }

  async goto() {
    await this.page.goto('https://www.bullvpn.com/login');
  }

  async login(username: string, password: string) {
    await this.usernameInput.fill(username);
    await this.passwordInput.fill(password);
    await this.page.pause();
    await this.loginButton.click();
  }
  
}