import type { INoRowsOverlayParams, IOverlay, IOverlayComp, IOverlayParams, OverlayComponentUserParams } from './overlayComponent';
import { OverlayComponent } from './overlayComponent';
export interface INoRowsOverlay<TData = any, TContext = any> extends IOverlay<TData, TContext, INoRowsOverlayParams<TData, TContext>> {
}
export interface INoRowsOverlayComp<TData = any, TContext = any> extends IOverlayComp<TData, TContext, INoRowsOverlayParams<TData, TContext>> {
}
export declare class NoRowsOverlayComponent extends OverlayComponent<any, any, IOverlayParams & OverlayComponentUserParams> implements INoRowsOverlayComp<any, any> {
    init(params: INoRowsOverlayParams & OverlayComponentUserParams): void;
}
