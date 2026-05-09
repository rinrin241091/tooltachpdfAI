import type { NamedBean } from '../context/bean';
import { BeanStub } from '../context/beanStub';
/** @internal AG_GRID_INTERNAL - Not for public use. Can change / be removed at any time. */
export declare class PageBoundsService extends BeanStub implements NamedBean {
    beanName: "pageBounds";
    private topRowBounds?;
    private bottomRowBounds?;
    private pixelOffset;
    getFirstRow(): number;
    getLastRow(): number;
    getCurrentPageHeight(): number;
    getCurrentPagePixelRange(): {
        pageFirstPixel: number;
        pageLastPixel: number;
    };
    calculateBounds(topDisplayedRowIndex: number, bottomDisplayedRowIndex: number): void;
    getPixelOffset(): number;
    private calculatePixelOffset;
}
