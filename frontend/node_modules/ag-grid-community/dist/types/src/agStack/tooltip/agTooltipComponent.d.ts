import type { AgCoreBeanCollection } from '../interfaces/agCoreBeanCollection';
import type { BaseEvents } from '../interfaces/baseEvents';
import type { BaseProperties } from '../interfaces/baseProperties';
import type { IComponent } from '../interfaces/iComponent';
import type { IPropertiesService } from '../interfaces/iProperties';
import { AgPopupComponent } from '../popup/agPopupComponent';
import type { BaseTooltipParams } from './baseTooltipStateManager';
/** @internal AG_GRID_INTERNAL - Not for public use. Can change / be removed at any time. */
export declare class AgTooltipComponent<TBeanCollection extends AgCoreBeanCollection<TProperties, TGlobalEvents, TCommon, TPropertiesService>, TProperties extends BaseProperties, TGlobalEvents extends BaseEvents, TCommon, TPropertiesService extends IPropertiesService<TProperties, TCommon>, TComponentSelectorType extends string, TTooltipParams extends BaseTooltipParams<TLocation>, TLocation extends string> extends AgPopupComponent<TBeanCollection, TProperties, TGlobalEvents, TCommon, TPropertiesService, TComponentSelectorType> implements IComponent<TTooltipParams> {
    constructor();
    init(params: TTooltipParams): void;
}
