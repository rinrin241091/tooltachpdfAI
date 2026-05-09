import type { UtilBeanCollection } from '../interfaces/agCoreBeanCollection';
/** @internal AG_GRID_INTERNAL - Not for public use. Can change / be removed at any time. */
export declare function _getRootNode(beans: UtilBeanCollection): Document | ShadowRoot;
/** @internal AG_GRID_INTERNAL - Not for public use. Can change / be removed at any time. */
export declare function _getActiveDomElement(beans: UtilBeanCollection): Element | null;
/** @internal AG_GRID_INTERNAL - Not for public use. Can change / be removed at any time. */
export declare function _getDocument(beans: UtilBeanCollection): Document;
/** @internal AG_GRID_INTERNAL - Not for public use. Can change / be removed at any time. */
export declare function _isNothingFocused(beans: UtilBeanCollection): boolean;
/** @internal AG_GRID_INTERNAL - Not for public use. Can change / be removed at any time. */
export declare function _getWindow(beans: UtilBeanCollection): Window & typeof globalThis;
/** @internal AG_GRID_INTERNAL - Not for public use. Can change / be removed at any time. */
export declare function _getPageBody(beans: UtilBeanCollection): HTMLElement | ShadowRoot;
export declare function _getBodyWidth(beans: UtilBeanCollection): number;
export declare function _getBodyHeight(beans: UtilBeanCollection): number;
