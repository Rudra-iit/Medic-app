import { Component, ElementRef, ViewChild } from '@angular/core';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import { CommonModule } from '@angular/common';

interface InvoiceItem {
  desc: string;
  qty: number;
  price: number;
}

@Component({
  selector: 'app-invoice',
  imports: [CommonModule],
  templateUrl: './invoice.html',
  styleUrls: ['./invoice.css']
})
export class Invoice {
  @ViewChild('invoiceEl') invoiceEl!: ElementRef<HTMLElement>;

  company = {
    name: 'Company Brand',
    address: '221B Baker Street, London',
    email: 'billing@companybrand.com',
    phone: '+44 20 7946 0958'
  };

  billTo = {
    name: 'Jane Doe',
    address: '742 Evergreen Terrace, Springfield',
    email: 'jane.doe@example.com'
  };

  meta = {
    number: 'INV-2026-0142',
    date: new Date(2026, 7, 12),
    dueDate: new Date(2026, 7, 26)
  };

  items: InvoiceItem[] = [
    { desc: '', qty: 1, price: 0 },
    { desc: '', qty: 1, price: 0 },
    { desc: '', qty: 1, price: 0 }
  ];

  taxRate = 0.075; // 7.5%

  get subtotal(): number {
    return this.items.reduce((sum, item) => sum + item.qty * item.price, 0);
  }

  get taxAmount(): number {
    return this.subtotal * this.taxRate;
  }

  get total(): number {
    return this.subtotal + this.taxAmount;
  }

  addItem(): void {
    this.items.push({ desc: '', qty: 1, price: 0 });
  }

  removeItem(index: number): void {
    if (this.items.length > 1) {
      this.items.splice(index, 1);
    }
  }

  async downloadInvoice(): Promise<void> {
    const el = this.invoiceEl.nativeElement;
    const canvas = await html2canvas(el, { scale: 2 });
    const imgData = canvas.toDataURL('image/png');

    const doc = new jsPDF('p', 'mm', 'a4');
    const pageWidth = doc.internal.pageSize.getWidth();
    const imgHeight = (canvas.height * pageWidth) / canvas.width;

    doc.addImage(imgData, 'PNG', 0, 0, pageWidth, imgHeight);
    doc.save(`${this.meta.number}.pdf`);
  }

  printInvoice(): void {
    window.print();
  }
}