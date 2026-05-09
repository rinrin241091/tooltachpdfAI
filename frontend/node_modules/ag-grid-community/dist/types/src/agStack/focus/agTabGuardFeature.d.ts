import { AgBeanStub } from '../core/agBeanStub';
import type { AgComponent } from '../interfaces/agComponent';
import type { AgCoreBeanCollection } from '../interfaces/agCoreBeanCollection';
import type { BaseEvents } from '../interfaces/baseEvents';
import type { BaseProperties } from '../interfaces/baseProperties';
import type { IPropertiesService } from '../interfaces/iProperties';
import type { StopPropagationCallbacks } from './agManagedFocusFeature';
import { AgTabGuardCtrl } from './tabGuardCtrl';
/** @internal AG_GRID_INTERNAL - Not for public use. Can change / be removed at any time. */
export interface AgTabGuardParams {
    focusInnerElement?: (fromBottom: boolean) => boolean;
    shouldStopEventPropagation?: () => boolean;
    /**
     * @returns `true` to prevent the default onFocusIn behavior
     */
    onFocusIn?: (e: FocusEvent) => void;
    /**
     * @returns `true` to prevent the default onFocusOut behavior
     */
    onFocusOut?: (e: FocusEvent) => void;
    onTabKeyDown?: (e: KeyboardEvent) => void;
    handleKeyDown?: (e: KeyboardEvent) => void;
    /**
     * By default will check for focusable elements to see if empty.
     * Provide this to override.
     */
    isEmpty?: () => boolean;
    /**
     * Set to true to create a circular focus pattern when keyboard tabbing.
     */
    focusTrapActive?: boolean;
    /**
     * Set to true to find a focusable element outside of the TabGuards to focus
     */
    forceFocusOutWhenTabGuardsAreEmpty?: boolean;
    isFocusableContainer?: boolean;
}
/** @internal AG_GRID_INTERNAL - Not for public use. Can change / be removed at any time. */
export declare class AgTabGuardFeature<TBeanCollection extends AgCoreBeanCollection<TProperties, TGlobalEvents, TCommon, TPropertiesService>, TProperties extends BaseProperties, TGlobalEvents extends BaseEvents, TCommon, TPropertiesService extends IPropertiesService<TProperties, TCommon>> extends AgBeanStub<TBeanCollection, TProperties, TGlobalEvents, TCommon, TPropertiesService> {
    private readonly comp;
    private readonly stopPropagationCallbacks?;
    private eTopGuard;
    private eBottomGuard;
    private eFocusableElement;
    private tabGuardCtrl;
    constructor(comp: AgComponent<TBeanCollection, TProperties, TGlobalEvents, any>, stopPropagationCallbacks?: StopPropagationCallbacks | undefined);
    initialiseTabGuard(params: AgTabGuardParams): void;
    getTabGuardCtrl(): AgTabGuardCtrl<TBeanCollection, TProperties, TGlobalEvents, TCommon, TPropertiesService>;
    private createTabGuard;
    private addTabGuards;
    removeAllChildrenExceptTabGuards(): void;
    forceFocusOutOfContainer(up?: boolean): void;
    appendChild(appendChild: (newChild: HTMLElement | AgComponent<TBeanCollection, TProperties, TGlobalEvents, any>, container?: HTMLElement) => void, newChild: AgComponent<TBeanCollection, TProperties, TGlobalEvents, any> | HTMLElement, container?: HTMLElement | undefined): void;
    destroy(): void;
}
