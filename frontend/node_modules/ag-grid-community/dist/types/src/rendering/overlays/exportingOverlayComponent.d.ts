import type { IExportingOverlayParams, IOverlay, IOverlayComp, IOverlayParams, OverlayComponentUserParams } from './overlayComponent';
import { OverlayComponent } from './overlayComponent';
export interface IExportingOverlay<TData = any, TContext = any> extends IOverlay<TData, TContext, IExportingOverlayParams<TData, TContext>> {
}
export interface IExportingOverlayComp<TData = any, TContext = any> extends IOverlayComp<TData, TContext, IExportingOverlayParams<TData, TContext>> {
}
export declare class ExportingOverlayComponent extends OverlayComponent<any, any, IOverlayParams & OverlayComponentUserParams> implements IExportingOverlayComp<any, any> {
    private readonly eExportingIcon;
    private readonly eExportingText;
    init(params: IExportingOverlayParams & OverlayComponentUserParams): void;
}
