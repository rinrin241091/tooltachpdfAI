import { AgPromise } from '../../agStack/utils/promise';
import type { LayoutView, UpdateLayoutClassesParams } from '../../styling/layoutFeature';
import type { ComponentSelector } from '../../widgets/component';
import { Component } from '../../widgets/component';
import type { IOverlayComp } from './overlayComponent';
export declare class OverlayWrapperComponent extends Component implements LayoutView {
    private eOverlayWrapper;
    activeOverlay: IOverlayComp | null;
    private activePromise;
    private activeCssClass;
    private elToFocusAfter;
    private overlayExclusive;
    private oldWrapperPadding;
    constructor();
    private handleKeyDown;
    updateLayoutClasses(cssClass: string, params: UpdateLayoutClassesParams): void;
    postConstruct(): void;
    private setWrapperTypeClass;
    showOverlay(overlayComponentPromise: AgPromise<IOverlayComp> | null, overlayWrapperCssClass: string, exclusive: boolean): AgPromise<IOverlayComp | undefined>;
    refreshWrapperPadding(): void;
    private destroyActiveOverlay;
    hideOverlay(): void;
    private isGridFocused;
    destroy(): void;
}
export declare const OverlayWrapperSelector: ComponentSelector;
