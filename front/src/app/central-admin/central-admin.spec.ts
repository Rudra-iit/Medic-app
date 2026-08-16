import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CentralAdmin } from './central-admin';

describe('CentralAdmin', () => {
  let component: CentralAdmin;
  let fixture: ComponentFixture<CentralAdmin>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CentralAdmin],
    }).compileComponents();

    fixture = TestBed.createComponent(CentralAdmin);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
