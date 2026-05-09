import type { IEnvironment } from '../interfaces/iEnvironment';
export declare const IS_SSR: boolean;
/** For testing, if true, only Vanilla examples will work and they will use legacy themes. */
export declare const FORCE_LEGACY_THEMES = false;
type InjectedStyle = {
    rawCss: string;
    injectedCss: string;
    el: HTMLStyleElement;
    priority: number;
    isParams: boolean;
};
export declare const _injectGlobalCSS: (rawCss: string, styleContainer: HTMLElement, debugId: string, layer: string | undefined, priority: number, nonce: string | undefined, isParams?: boolean) => void;
export declare const _injectCoreAndModuleCSS: (styleContainer: HTMLElement, layer: string | undefined, nonce: string | undefined, moduleCss: Map<string, string[]> | undefined) => void;
export declare const _useParamsCss: (environment: IEnvironment, paramsCss: string | null, paramsDebugId: string | null, styleContainer: HTMLElement, layer: string | undefined, nonce: string | undefined) => void;
export declare const _unregisterInstanceUsingThemingAPI: (environment: IEnvironment) => void;
type InjectedGridCssState = {
    styleContainer: HTMLElement;
    paramsCss: string | null;
};
type InjectionState = {
    map: WeakMap<HTMLElement, InjectedStyle[]>;
    grids: Map<IEnvironment, InjectedGridCssState>;
    paramsId: number;
};
export declare const getInjectionState: () => InjectionState;
export {};
