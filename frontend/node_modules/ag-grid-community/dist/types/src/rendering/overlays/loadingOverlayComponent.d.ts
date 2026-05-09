import type { ILoadingOverlayParams, IOverlay, IOverlayComp, IOverlayParams, OverlayComponentUserParams } from './overlayComponent';
import { OverlayComponent } from './overlayComponent';
export interface ILoadingOverlay<TData = any, TContext = any> extends IOverlay<TData, TContext, ILoadingOverlayParams<TData, TContext>> {
}
export interface ILoadingOverlayComp<TData = any, TContext = any> extends IOverlayComp<TData, TContext, ILoadingOverlayParams<TData, TContext>> {
}
export declare class LoadingOverlayComponent extends OverlayComponent<any, any, IOverlayParams & OverlayComponentUserParams> implements ILoadingOverlayComp<any, any> {
    private readonly eLoadingIcon;
    private readonly eLoadingText;
    init(params: ILoadingOverlayParams & OverlayComponentUserParams): void;
}
