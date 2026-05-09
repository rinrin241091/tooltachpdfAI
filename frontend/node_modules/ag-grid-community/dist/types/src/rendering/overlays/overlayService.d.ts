import type { NamedBean } from '../../context/bean';
import { BeanStub } from '../../context/beanStub';
import type { ComponentSelector } from '../../widgets/component';
import { OverlayWrapperComponent } from './overlayWrapperComponent';
export declare class OverlayService extends BeanStub implements NamedBean {
    beanName: "overlays";
    eWrapper: OverlayWrapperComponent | undefined;
    exclusive: boolean;
    private oldExclusive;
    private currentDef;
    private showInitialOverlay;
    private userForcedNoRows;
    private exportsInProgress;
    private focusedCell;
    private newColumnsLoadedCleanup;
    postConstruct(): void;
    destroy(): void;
    setWrapperComp(overlayWrapperComp: OverlayWrapperComponent, destroyed: boolean): void;
    /** Returns true if the overlay is visible. */
    isVisible(): boolean;
    showLoadingOverlay(): void;
    showNoRowsOverlay(): void;
    showExportOverlay(heavyOperation: () => void): Promise<void>;
    hideOverlay(): void;
    getOverlayWrapperSelector(): ComponentSelector;
    getOverlayWrapperCompClass(): typeof OverlayWrapperComponent;
    private onPropChange;
    private updateOverlay;
    private getDesiredDefWithOverride;
    private getOverlayDef;
    private disableInitialOverlay;
    /**
     * Show an overlay requested by name or by built-in types.
     * This single function replaces the previous three helpers and handles
     * param selection and wrapper class choice for loading / no-rows and custom overlays.
     */
    private doShowOverlay;
    private makeCompParams;
    private doHideOverlay;
    private setExclusive;
    private isDisabled;
}
