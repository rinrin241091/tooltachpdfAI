import type { INoMatchingRowsOverlayParams, IOverlay, IOverlayComp, IOverlayParams, OverlayComponentUserParams } from './overlayComponent';
import { OverlayComponent } from './overlayComponent';
export interface INoMatchingRowsOverlay<TData = any, TContext = any> extends IOverlay<TData, TContext, INoMatchingRowsOverlayParams<TData, TContext>> {
}
export interface INoMatchingRowsOverlayComp<TData = any, TContext = any> extends IOverlayComp<TData, TContext, INoMatchingRowsOverlayParams<TData, TContext>> {
}
export declare class NoMatchingRowsOverlayComponent extends OverlayComponent<any, any, IOverlayParams & OverlayComponentUserParams> implements INoMatchingRowsOverlayComp<any, any> {
    init(params: INoMatchingRowsOverlayParams & OverlayComponentUserParams): void;
}
